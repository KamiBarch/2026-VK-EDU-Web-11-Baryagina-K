from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import Http404
from datetime import timedelta
from django.utils import timezone


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    return paginator.get_page(request.GET.get('page', 1))

TAGS = {
    'pr': {'slug': 'pr', 'name': 'PR'},
    'yav26': {'slug': 'yav26', 'name': 'ЯВ26'},
    'bestalks': {'slug': 'bestalks', 'name': 'BESTALKS'},
}

ANSWERS = [
    {
        'id': i,
        'text': f'Это текст ответа {i} на заданный вопрос.',
        'created_at': timezone.now() - timedelta(hours=i),
    }
    for i in range(1, 15)
]

QUESTIONS = [
    {
        'id': i,
        'title': f'Вопрос {i}: Как составить PR-стратегию?',
        'text': f'Описание вопроса {i}. Ребята, собираем Core-team...',
        'tags': (
            [TAGS['pr'], TAGS['yav26']]
            if i % 2 == 1
            else [TAGS['bestalks']]
        ),
        'answers_count': len(ANSWERS),
        'created_at': timezone.now() - timedelta(hours=i),

    }
    for i in range(1, 36)
]



def index(request):
    page = paginate(QUESTIONS, request, per_page=5)
    return render(request, 'core/index.html', {'page_obj': page, 'page_title': 'New Questions', 'user': {'is_authenticated': True}})

def hot_questions(request):
    page = paginate(QUESTIONS[::-1], request, per_page=5)
    return render(request, 'core/index.html', {'page_obj': page, 'page_title': 'Hot Questions', 'user': {'is_authenticated': True}})

def tag_questions(request, tag_name):
    filtered_questions = [
        question
        for question in QUESTIONS
        if any(tag['slug'] == tag_name for tag in question['tags'])
    ]
    page = paginate(filtered_questions, request, per_page=5)
    tag_title = TAGS.get(tag_name, {}).get('name', tag_name)
    return render(request, 'core/index.html', {'page_obj': page, 'page_title': f'Tag: {tag_title}', 'tag_name': tag_name, 'user': {'is_authenticated': True}})

def question_detail(request, question_id):
    question = next((question for question in QUESTIONS if question['id'] == question_id),None,)
    if question is None:
        raise Http404('Вопрос не найден')
    answers_page = paginate(ANSWERS, request, per_page=5)
    return render(request, 'core/question.html', {
        'question': question, 
        'page_obj': answers_page, 
        'user': {'is_authenticated': True}
    })

def ask_view(request):
    return render(request, 'core/ask.html', {'user': {'is_authenticated': True}})