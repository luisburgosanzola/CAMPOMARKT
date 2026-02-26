## consulta de protocolo de segurida en python de registro

## peticiones para agregar productos
POST http://127.0.0.1:8000/api/fichas/agregar/

{
  "cultivo": "Papa",
  "problema": "Tizón tardío",
  "descripcion": "Enfermedad causada por Phytophthora infestans.",
  "recomendacion": "Aplicar fungicidas preventivos y rotar cultivos.",
  "fuente": "Manual técnico ICA 2024"
}

## pericion para consultar productos

GET http://127.0.0.1:8000/api/fichas/listar/