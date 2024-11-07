from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Income
from .serializers import IncomeSerializer

@api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])  # מאפשר גישה רק למשתמשים מחוברים
def income_list(request):
    if request.method == 'GET':
        incomes = Income.objects.filter()
        serializer = IncomeSerializer(incomes, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = IncomeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
# @permission_classes([IsAuthenticated])  # מאפשר גישה רק למשתמשים מחוברים
def income_detail(request, pk):
    try:
        income = Income.objects.get(pk=pk)
    except Income.DoesNotExist:
        return Response({'error': 'Income not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = IncomeSerializer(income)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = IncomeSerializer(income, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        income.delete()
        return Response({'message': 'Income deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
