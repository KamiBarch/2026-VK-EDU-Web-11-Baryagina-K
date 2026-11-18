from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe
from django.core.paginator import Paginator

from .models import Answer, Question, Tag

def paginate(queryset, request, per_page=5):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page", 1))


def render_question_list(request, queryset, title, active_tab=None):
    return render(request, "core/index.html", {
        "page_obj": paginate(queryset.for_cards(), request),
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


@require_safe
def question_detail(request, question_id):
    question = get_object_or_404(Question.objects.with_author_and_tags(), pk=question_id)
    page = paginate(Answer.objects.for_question(question), request)
    return render(request, "core/question.html", {"question": question, "page_obj": page})


@require_safe
def ask_view(request):
    return render(request, "core/ask.html")