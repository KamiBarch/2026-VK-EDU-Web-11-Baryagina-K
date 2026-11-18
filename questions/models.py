from django.conf import settings
from django.db import models
from django.urls import reverse
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce


class Tag(models.Model):
    name = models.CharField("название", max_length=100)
    slug = models.SlugField("адресное имя", max_length=100, unique=True)

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class QuestionQuerySet(models.QuerySet):
    def new(self):
        return self.order_by("-created_at", "-pk")

    def best(self):
        return self.order_by("-rating", "-created_at", "-pk")

    def by_tag(self, slug):
        return self.filter(tags__slug=slug)

    def with_author_and_tags(self):
        return self.select_related("author__profile").prefetch_related("tags")

    def for_cards(self):
        answer_counts = (
            Answer.objects.filter(question_id=OuterRef("pk"))
            .order_by()
            .values("question_id")
            .annotate(total=Count("pk"))
            .values("total")
        )
        return self.with_author_and_tags().annotate(
            answers_count=Coalesce(Subquery(answer_counts), 0)
        )


class Question(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="автор",
    )
    title = models.CharField("заголовок", max_length=100)
    text = models.TextField("текст", max_length=1000)
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    tags = models.ManyToManyField(
        Tag, related_name="questions", verbose_name="теги", blank=True
    )
    rating = models.IntegerField("рейтинг", default=0, editable=False)

    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = "вопрос"
        verbose_name_plural = "вопросы"
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(fields=["-created_at", "-id"], name="question_new_idx"),
            models.Index(
                fields=["-rating", "-created_at", "-id"],
                name="question_best_idx",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("question", kwargs={"question_id": self.pk})

class AnswerQuerySet(models.QuerySet):
    def for_question(self, question):
        return (
            self.filter(question=question)
            .select_related("author__profile")
            .order_by("created_at", "pk")
        )

class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="вопрос",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="автор",
    )
    text = models.TextField("текст", max_length=1500)
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    is_correct = models.BooleanField("правильный ответ", default=False)
    rating = models.IntegerField("рейтинг", default=0, editable=False)
    
    objects = AnswerQuerySet.as_manager()

    class Meta:
        verbose_name = "ответ"
        verbose_name_plural = "ответы"
        ordering = ["created_at", "pk"]
        indexes = [
            models.Index(
                fields=["question", "created_at", "id"], name="answer_page_idx"
            ),
        ]

    def __str__(self):
        return f"Ответ {self.pk} на вопрос {self.question_id}"


class QuestionLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_likes",
        verbose_name="пользователь",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="вопрос",
    )
    value = models.SmallIntegerField(
        "оценка", choices=[(1, "Плюс"), (-1, "Минус")], default=1
    )

    class Meta:
        verbose_name = "оценка вопроса"
        verbose_name_plural = "оценки вопросов"
        unique_together = [("user", "question")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(value__in=[-1, 1]),
                name="question_like_value_valid",
            ),
        ]

    def __str__(self):
        return f"Оценка {self.value}: вопрос {self.question_id}, пользователь {self.user_id}"


class AnswerLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answer_likes",
        verbose_name="пользователь",
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="ответ",
    )
    value = models.SmallIntegerField(
        "оценка", choices=[(1, "Плюс"), (-1, "Минус")], default=1
    )

    class Meta:
        verbose_name = "оценка ответа"
        verbose_name_plural = "оценки ответов"
        unique_together = [("user", "answer")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(value__in=[-1, 1]),
                name="answer_like_value_valid",
            ),
        ]

    def __str__(self):
        return f"Оценка {self.value}: ответ {self.answer_id}, пользователь {self.user_id}"
