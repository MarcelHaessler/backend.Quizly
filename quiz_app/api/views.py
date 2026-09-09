from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import Quiz
from ..utils import create_quiz_from_url, QuizGenerationError
from .permissions import IsQuizOwner
from .serializers import QuizCreateSerializer, QuizSerializer

GENERATION_FAILED = {'detail': 'Could not generate a quiz from this video.'}


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Returns, updates or deletes a single quiz."""

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsQuizOwner, IsAuthenticated]


class QuizListCreateView(generics.ListCreateAPIView):
    """Lists the user's quizzes and creates a new one from a YouTube URL."""

    serializer_class = QuizSerializer

    def get_queryset(self):
        return Quiz.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        eingabe = QuizCreateSerializer(data=request.data)
        eingabe.is_valid(raise_exception=True)
        try:
            quiz = create_quiz_from_url(request.user, eingabe.validated_data['url'])
        except QuizGenerationError:
            return Response(GENERATION_FAILED, status=status.HTTP_400_BAD_REQUEST)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)