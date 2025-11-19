from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Bairro
from .serializers import BairroSerializer

class BairrosAPIView(APIView):
    def get(self, request):
        dia = request.GET.get("dia")
        bairro = request.GET.get("bairro")
        
        bairros = Bairro.objects.all()

        if dia:
            dia = dia.lower()
            filtrados = []
            for b in bairros:
                dias = b.properties.get("Dias")
                if dias and any(dia == d.lower() for d in dias):
                    filtrados.append(b)
            bairros = filtrados

        if bairro:
            bairro = bairro.lower()
            filtrados = []
            for b in bairros:
                bairro_ = b.properties.get("Bairro")
                if bairro_ and bairro == bairro_.lower():
                    filtrados.append(b)
            bairros = filtrados

        serializer = BairroSerializer(bairros, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)