from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (require_http_methods, require_safe,)
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.translation import override

from django.contrib.auth.views import redirect_to_login
from django.db.models import OuterRef, Q, Subquery
from django.http import JsonResponse
from .forms import AnswerForm, AnswerVoteForm, QuestionForm, QuestionVoteForm
from .models import Answer, AnswerLike, Question, QuestionLike, Tag
from .forms import AnswerApprovalForm
from django.core.exceptions import PermissionDenied




def answer_vote(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Use POST to vote."},
            status=405,
            headers={"Allow": "POST"},
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Log in to vote."},
            status=401,
        )

    form = AnswerVoteForm(request.POST)

    if not form.is_valid():
        errors = form.errors.get_json_data()
        first_error = next(iter(errors.values()))[0]["message"]

        return JsonResponse(
            {"error": first_error},
            status=400,
        )

    try:
        rating, value, changed = form.save(request.user)
    except Answer.DoesNotExist:
        return JsonResponse(
            {"error": "Answer not found."},
            status=404,
        )

    if not changed:
        return JsonResponse(
            {
                "error": "You already selected this vote.",
                "rating": rating,
                "value": value,
            },
            status=409,
        )

    return JsonResponse(
        {
            "rating": rating,
            "value": value,
        }
    )

def question_vote(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Use POST to vote."},
            status=405,
            headers={"Allow": "POST"},
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Log in to vote."},
            status=401,
        )

    form = QuestionVoteForm(request.POST)

    if not form.is_valid():
        errors = form.errors.get_json_data()
        first_error = next(iter(errors.values()))[0]["message"]

        return JsonResponse(
            {"error": first_error},
            status=400,
        )

    try:
        rating, value, changed = form.save(request.user)
    except Question.DoesNotExist:
        return JsonResponse(
            {"error": "Question not found."},
            status=404,
        )

    if not changed:
        return JsonResponse(
            {
                "error": "You already selected this vote.",
                "rating": rating,
                "value": value,
            },
            status=409,
        )


    return JsonResponse(
        {
            "rating": rating,
            "value": value,
        }
    )


def paginate(queryset, request, per_page=5):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page", 1))

def with_my_question_vote(queryset, user):
    if not user.is_authenticated:
        return queryset

    votes = QuestionLike.objects.filter(
        question_id=OuterRef("pk"),
        user_id=user.pk,
    ).values("value")[:1]

    return queryset.annotate(
        my_vote=Subquery(votes),
    )
def render_question_list(request, queryset, title, active_tab=None):
    return render(request, "core/index.html", {
        "page_obj": paginate(with_my_question_vote(queryset.for_cards(), request.user),request,),
        "page_title": title,
        "active_tab": active_tab,
    })


@require_safe
def index(request):
    return render_question_list(request, Question.objects.new(), "New questions", "new")


@require_safe
def hot_questions(request):
    return render_question_list(request, Question.objects.best(), "Hot questions", "hot")


@require_safe
def tag_questions(request, tag_name):
    tag = get_object_or_404(Tag, slug=tag_name)
    questions = Question.objects.by_tag(tag.slug).new()
    return render_question_list(request, questions, f"Tags: {tag.name}")

ANSWERS_PER_PAGE = 5

@require_http_methods(["GET", "HEAD", "POST"])
def question_detail(request, question_id):
    with override("en"):
        if request.method == "POST" and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        questions = with_my_question_vote(
            Question.objects.with_author_and_tags(),
            request.user,
        )

        question = get_object_or_404(
            questions,
            pk=question_id,
        )


        if request.method == "POST":
            form = AnswerForm(request.user, question, request.POST)

            if form.is_valid():
                answer = form.save()

                before = (
                    Answer.objects
                    .filter(question_id=question.pk)
                    .filter(
                        Q(created_at__lt=answer.created_at)
                        | Q(
                            created_at=answer.created_at,
                            pk__lt=answer.pk,
                        )
                    )
                    .count()
                )

                page_number = before // ANSWERS_PER_PAGE + 1

                return redirect(
                    f"{question.get_absolute_url()}"
                    f"?page={page_number}#answer-{answer.pk}"
                )
        else:
            form = AnswerForm(request.user, question)

        answers = Answer.objects.for_question(question)
        if request.user.is_authenticated:
            votes = AnswerLike.objects.filter(
                answer_id=OuterRef("pk"),
                user_id=request.user.pk,
            ).values("value")[:1]
            answers = answers.annotate(
                my_vote=Subquery(votes),
            )
        page = paginate(
            answers,
            request,
            per_page=ANSWERS_PER_PAGE,
        )

        return render(
            request,
            "core/question.html",
            {
                "question": question,
                "page_obj": page,
                "answer_form": form,
            },
        )

@login_required
@require_http_methods(["GET", "HEAD", "POST"])
def ask_view(request):
    with override("en"):
        if request.method == "POST":
            form = QuestionForm(request.user, request.POST)

            if form.is_valid():
                question = form.save()
                return redirect(question.get_absolute_url())
        else:
            form = QuestionForm(request.user)

        return render(
            request,
            "core/ask.html",
            {"form": form},
        )


def answer_approval(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Use POST to change approval.",
            },
            status=405,
            headers={"Allow": "POST"},
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "error": "Log in to approve an answer.",
            },
            status=401,
        )

    form = AnswerApprovalForm(request.POST)

    if not form.is_valid():
        errors = form.errors.get_json_data()

        return JsonResponse(
            {
                "error": next(iter(errors.values()))[0]["message"],
            },
            status=400,
        )

    try:
        approved_answer_id = form.save(request.user)

    except PermissionDenied:
        return JsonResponse(
            {
                "error": "Only the question author can approve an answer.",
            },
            status=403,
        )

    except Question.DoesNotExist:
        return JsonResponse(
            {
                "error": "Question not found.",
            },
            status=404,
        )

    except Answer.DoesNotExist:
        return JsonResponse(
            {
                "error": "Answer not found in this question.",
            },
            status=404,
        )

    return JsonResponse(
        {
            "approved_answer_id": (
                None
                if approved_answer_id is None
                else str(approved_answer_id)
            ),
        }
    )
