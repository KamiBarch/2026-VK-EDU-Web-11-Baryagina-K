from hashlib import sha256
from django import forms
from django.db import transaction
from django.utils.text import slugify

from .models import Answer, AnswerLike, Question, QuestionLike, Tag
from django.core.exceptions import PermissionDenied


class QuestionForm(forms.ModelForm):
    tags_text = forms.CharField(
        required=False,
        max_length=1000,
    )

    class Meta:
        model = Question
        fields = ("title", "text")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_tags_text(self):
        tags = {}

        for raw_tag in self.cleaned_data["tags_text"].split(","):
            name = " ".join(raw_tag.split())

            if not name:
                continue

            if len(name) > 100:
                raise forms.ValidationError(
                    "Each tag must be 100 characters or fewer."
                )

            if not any(char.isalnum() for char in name):
                raise forms.ValidationError(
                    "Each tag must contain a letter or a number."
                )

            key = name.casefold()
            slug = slugify(key)

            if not slug or slug != key.replace(" ", "-"):
                digest = sha256(
                    key.encode("utf-8")
                ).hexdigest()[:24]
                slug = f"tag-{digest}"

            tags.setdefault(slug, name)

        return tags

    @transaction.atomic
    def save(self):
        question = super().save(commit=False)
        question.author = self.user
        question.save()

        for slug, name in self.cleaned_data["tags_text"].items():
            tag, _ = Tag.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )
            question.tags.add(tag)

        return question

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ("text",)

    def __init__(self, user, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.question = question

    def save(self):
        answer = super().save(commit=False)
        answer.author = self.user
        answer.question = self.question
        answer.save()
        return answer

class QuestionVoteForm(forms.Form):
    question_id = forms.IntegerField(
        min_value=1,
        max_value=2**63 - 1,
    )
    value = forms.TypedChoiceField(
        choices=(
            (1, "Like"),
            (-1, "Dislike"),
        ),
        coerce=int,
    )

    @transaction.atomic
    def save(self, user):
        question = Question.objects.select_for_update().get(
            pk=self.cleaned_data["question_id"]
        )

        new_value = self.cleaned_data["value"]

        vote, created = QuestionLike.objects.get_or_create(
            user=user,
            question=question,
            defaults={"value": new_value},
        )

        old_value = 0 if created else vote.value

        if old_value == new_value:
            return question.rating, vote.value, False

        if not created:
            vote.value = new_value
            vote.save(update_fields=["value"])

        question.rating += new_value - old_value
        question.save(update_fields=["rating"])

        return question.rating, new_value, True

class AnswerVoteForm(forms.Form):
    answer_id = forms.IntegerField(
        min_value=1,
        max_value=2**63 - 1,
    )
    value = forms.TypedChoiceField(
        choices=(
            (1, "Like"),
            (-1, "Dislike"),
        ),
        coerce=int,
    )

    @transaction.atomic
    def save(self, user):
        answer = Answer.objects.select_for_update().get(
            pk=self.cleaned_data["answer_id"]
        )

        new_value = self.cleaned_data["value"]

        vote, created = AnswerLike.objects.get_or_create(
            user=user,
            answer=answer,
            defaults={"value": new_value},
        )

        old_value = 0 if created else vote.value

        if old_value == new_value:
            return answer.rating, vote.value, False

        if not created:
            vote.value = new_value
            vote.save(update_fields=["value"])

        answer.rating += new_value - old_value
        answer.save(update_fields=["rating"])

        return answer.rating, new_value, True

class AnswerApprovalForm(forms.Form):
    question_id = forms.IntegerField(min_value=1)
    answer_id = forms.IntegerField(min_value=1)
    approved = forms.TypedChoiceField(
        choices=(
            ("1", "Approve"),
            ("0", "Unapprove"),
        ),
        coerce=lambda value: value == "1",
    )

    @transaction.atomic
    def save(self, user):
        question = Question.objects.select_for_update().get(
            pk=self.cleaned_data["question_id"]
        )

        if question.author_id != user.pk:
            raise PermissionDenied

        answers = Answer.objects.filter(question_id=question.pk)
        answer = answers.get(pk=self.cleaned_data["answer_id"])

        if self.cleaned_data["approved"]:
            answers.filter(
                is_correct=True
            ).exclude(
                pk=answer.pk
            ).update(
                is_correct=False
            )

            answers.filter(
                pk=answer.pk,
                is_correct=False,
            ).update(
                is_correct=True
            )

            return answer.pk

        answers.filter(
            pk=answer.pk,
            is_correct=True,
        ).update(
            is_correct=False
        )

        return None

