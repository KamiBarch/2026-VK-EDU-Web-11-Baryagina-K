from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate(objects_list, request, per_page=10):
    page_number = request.GET.get('page', 1)
    paginator = Paginator(objects_list, per_page)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page

QUESTIONS = []
for i in range(1, 30):
    QUESTIONS.append({
        'id': i,
        'title': f'Вопрос {i}: Как составить PR-стратегию?',
        'text': f'Описание вопроса {i}. Ребята, собираем Core-team...',
        'tags': ['PR', 'ЯВ26'],
        'answers_count': 3
    })

ANSWERS = []
for i in range(1, 15):
    ANSWERS.append({
        'id': i,
        'text': f'Это текст ответа {i} на заданный вопрос.',
    })

def index(request):
    page = paginate(QUESTIONS, request, per_page=5)
    return render(request, 'core/index.html', {'page_obj': page, 'page_title': 'New Questions', 'user': {'is_authenticated': True}})

def hot_questions(request):
    page = paginate(QUESTIONS[::-1], request, per_page=5)
    return render(request, 'core/index.html', {'page_obj': page, 'page_title': 'Hot Questions', 'user': {'is_authenticated': True}})

def tag_questions(request, tag_name):
    page = paginate(QUESTIONS, request, per_page=5)
    return render(request, 'core/index.html', {'page_obj': page, 'page_title': f'Tag: {tag_name}', 'tag_name': tag_name, 'user': {'is_authenticated': True}})

def question_detail(request, question_id):
    question = next((q for q in QUESTIONS if q['id'] == question_id), QUESTIONS[0])
    answers_page = paginate(ANSWERS, request, per_page=5)
    return render(request, 'core/question.html', {
        'question': question, 
        'page_obj': answers_page, 
        'user': {'is_authenticated': True}
    })

def ask_view(request):
    return render(request, 'core/ask.html', {'user': {'is_authenticated': True}})