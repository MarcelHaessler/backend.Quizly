from rest_framework import serializers

from ..models import Question, Quiz
from ..utils import extract_video_id


class QuestionSerializer(serializers.ModelSerializer):
    """Serializes a single multiple-choice question."""

    class Meta:
        model = Question
        fields = [
            'id',
            'question_title',
            'question_options',
            'answer',
            'created_at',
            'updated_at',
        ]


class QuizSerializer(serializers.ModelSerializer):
    """Serializes a quiz including its nested questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'updated_at',
            'video_url',
            'questions',
        ]
        read_only_fields = ['video_url']


class QuizCreateSerializer(serializers.Serializer):
    """Validates the YouTube URL a new quiz is generated from."""

    url = serializers.URLField()

    def validate_url(self, value):
        """Rejects links that carry no YouTube video id."""
        if extract_video_id(value) is None:
            raise serializers.ValidationError('Only YouTube URLs are supported.')
        return value
