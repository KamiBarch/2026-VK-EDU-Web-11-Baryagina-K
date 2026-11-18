from django.contrib import admin
from django.db.models import Count

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class UsedTagFilter(admin.SimpleListFilter):
    title = "используется"
    parameter_name = "used"

    def lookups(self, request, model_admin):
        return (
            ("yes", "есть вопросы"),
            ("no", "нет вопросов"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(questions__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(questions__isnull=True)
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    list_filter = (UsedTagFilter,)
    ordering = ("name", "pk")


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    show_change_link = True
    fields = ("author", "text", "is_correct", "rating", "created_at")
    readonly_fields = ("created_at", "rating")
    autocomplete_fields = ("author",)
    ordering = ("created_at", "pk")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "rating", "answers_count", "created_at")
    search_fields = ("title", "text", "author__username")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("author", "tags")
    inlines = (AnswerInline,)
    list_select_related = ("author",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("author")
            .annotate(_answers_count=Count("answers", distinct=True))
        )

    @admin.display(ordering="_answers_count", description="ответов")
    def answers_count(self, obj):
        return obj._answers_count


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "author",
        "is_correct",
        "rating",
        "created_at",
    )
    search_fields = ("text", "question__title", "author__username")
    list_filter = ("is_correct", "created_at")
    date_hierarchy = "created_at"
    autocomplete_fields = ("question", "author")
    list_select_related = ("question", "author")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("question", "author")


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question", "value")
    search_fields = ("user__username", "question__title")
    list_filter = ("value",)
    autocomplete_fields = ("user", "question")
    list_select_related = ("user", "question")


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "answer", "value")
    search_fields = ("user__username", "answer__text")
    list_filter = ("value",)
    autocomplete_fields = ("user", "answer")
    list_select_related = ("user", "answer")
