from itertools import islice
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from faker import Faker

from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag
from core.models import Profile


BATCH_SIZE = 1000


def batches(items):
    iterator = iter(items)
    while batch := list(islice(iterator, BATCH_SIZE)):
        yield batch


def insert(model, items):
    for batch in batches(items):
        model.objects.bulk_create(batch, batch_size=BATCH_SIZE)


def vote_value(target_index, slot):
    return -1 if (target_index * 7 + slot * 11) % 23 < target_index % 22 else 1


def vote_total(target_index, count):
    return sum(vote_value(target_index, slot) for slot in range(count))


def question_votes(questions, start, user_ids, votes_per_question):
    for index, question in enumerate(questions, start=start):
        for slot in range(votes_per_question):
            yield QuestionLike(
                question_id=question.pk,
                user_id=user_ids[(index + slot) % len(user_ids)],
                value=vote_value(index, slot),
            )


def answer_votes(answers, start, user_ids, base_votes, extra_votes):
    for index, answer in enumerate(answers, start=start):
        for slot in range(base_votes + int(index < extra_votes)):
            yield AnswerLike(
                answer_id=answer.pk,
                user_id=user_ids[(index + slot) % len(user_ids)],
                value=vote_value(index, slot),
            )


class Command(BaseCommand):
    help = "Добавляет учебные данные BEST FAQ; существующие записи не удаляются."

    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int, help="Коэффициент заполнения, минимум 2.")

    def handle(self, *args, **options):
        ratio = options["ratio"]
        if ratio < 2:
            raise CommandError("Укажи целое ratio не меньше 2, например 10.")
        if not connection.features.can_return_rows_from_bulk_insert:
            raise CommandError("База должна возвращать PK после bulk_create; используй PostgreSQL.")

        fake = Faker("ru_RU")
        prefix = f"seed-{uuid4().hex}"
        question_count = 10 * ratio
        answer_count = 100 * ratio
        total_votes = 200 * ratio
        votes_per_question = min(10, ratio - 1)
        question_like_count = question_count * votes_per_question
        answer_like_count = total_votes - question_like_count
        base_votes, extra_votes = divmod(answer_like_count, answer_count)

        self.stdout.write(f"Порция: {prefix}. Добавляем данные, старые не удаляем.")
        with transaction.atomic():
            user_ids, tag_ids = self.add_users_and_tags(fake, prefix, ratio)
            self.stdout.write(f"Подготовлено пользователей, профилей и тегов: по {ratio}.")
            question_ids = self.add_questions(
                fake, question_count, user_ids, tag_ids, votes_per_question,
            )
            self.stdout.write(f"Подготовлено вопросов: {question_count}.")
            self.add_answers(
                fake, answer_count, user_ids, question_ids, base_votes, extra_votes,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Добавлено: пользователей {ratio}, профилей {ratio}, тегов {ratio}, "
            f"вопросов {question_count}, ответов {answer_count}, "
            f"связей вопрос–тег {2 * question_count}, "
            f"оценок вопросов {question_like_count}, оценок ответов {answer_like_count}, "
            f"всего оценок {total_votes}."
        ))

    def add_users_and_tags(self, fake, prefix, ratio):
        User = get_user_model()
        user_ids = []
        tag_ids = []

        users = (
            User(
                username=f"{prefix}-{index}",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password=make_password(None),
                is_active=True,
            )
            for index in range(ratio)
        )
        for batch in batches(users):
            User.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            user_ids.extend(user.pk for user in batch)
            insert(Profile, (Profile(user_id=user.pk) for user in batch))

        tags = (
            Tag(name=f"{fake.word().capitalize()} {index}", slug=f"{prefix}-{index}")
            for index in range(ratio)
        )
        for batch in batches(tags):
            Tag.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            tag_ids.extend(tag.pk for tag in batch)
        return user_ids, tag_ids

    def add_questions(self, fake, count, user_ids, tag_ids, votes_per_question):
        through = Question.tags.through
        question_ids = []
        questions = (
            Question(
                author_id=user_ids[index % len(user_ids)],
                title=fake.sentence(nb_words=6).rstrip(".")[:99] + "?",
                text=" ".join(fake.sentences(nb=2))[:1000],
                rating=vote_total(index, votes_per_question),
            )
            for index in range(count)
        )
        for start, batch in enumerate(batches(questions)):
            offset = start * BATCH_SIZE
            Question.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            question_ids.extend(question.pk for question in batch)
            insert(through, (
                through(question_id=question.pk, tag_id=tag_ids[(index + shift) % len(tag_ids)])
                for index, question in enumerate(batch, start=offset)
                for shift in (0, 1)
            ))
            insert(QuestionLike, question_votes(batch, offset, user_ids, votes_per_question))
        return question_ids

    def add_answers(self, fake, count, user_ids, question_ids, base_votes, extra_votes):
        answers = (
            Answer(
                question_id=question_ids[index // 10],
                author_id=user_ids[(index // 10 + index % 10 + 1) % len(user_ids)],
                text=" ".join(fake.sentences(nb=2))[:1500],
                is_correct=index % 10 == 0,
                rating=vote_total(index, base_votes + int(index < extra_votes)),
            )
            for index in range(count)
        )
        for batch_number, batch in enumerate(batches(answers)):
            offset = batch_number * BATCH_SIZE
            Answer.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            insert(AnswerLike, answer_votes(batch, offset, user_ids, base_votes, extra_votes))
            written = offset + len(batch)
            if written % 100_000 == 0 or written == count:
                self.stdout.write(f"Подготовлено ответов: {written} из {count}.")