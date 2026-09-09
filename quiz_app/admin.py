from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Lets questions be edited directly inside the quiz page."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin view for quizzes including their questions."""

    list_display = ('title', 'owner', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin view for editing single questions."""

    list_display = ('question_title', 'quiz', 'answer')
    list_filter = ('quiz',)
    search_fields = ('question_title',)
