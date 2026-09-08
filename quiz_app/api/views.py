from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Quiz
from .permissions import IsQuizOwner
from .serializers import QuizSerializer


class QuizListView(generics.ListAPIView):
    """Returns all quizzes belonging to the requesting user."""

    serializer_class = QuizSerializer

    def get_queryset(self):
        return Quiz.objects.filter(owner=self.request.user)


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Returns, updates or deletes a single quiz."""

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsQuizOwner, IsAuthenticated]