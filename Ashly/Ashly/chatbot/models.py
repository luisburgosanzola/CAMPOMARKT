from django.db import models
from app.Usuarios.models import User


# ======================================================
# ENUMS / TABLAS DE APOYO
# ======================================================

class PhenologicalStage(models.TextChoices):
    ESTABLISHMENT = "establecimiento", "Establecimiento / plántula"
    VEGETATIVE = "vegetativo", "Crecimiento vegetativo"
    FLOWERING = "floracion", "Floración"
    FRUIT_SET = "cuajado", "Cuajado de fruto"
    FRUITING = "fructificacion", "Fructificación / llenado"
    MATURITY = "madurez", "Madurez / pre-cosecha"


class IrrigationSystem(models.TextChoices):
    DRIP = "goteo", "Riego por goteo"
    SPRINKLER = "aspersion", "Aspersión"
    FURROW = "surcos", "Riego por surcos"
    MICRO_SPRINKLER = "microaspersores", "Microaspersores"
    OTHER = "otro", "Otro"


class Region(models.Model):
    """
    Para asociar recomendaciones por región o zona agroecológica.
    Ej: 'Huila - zona cafetera', 'Cundinamarca alta', etc.
    """
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ======================================================
# 1️⃣ Cultivos
# ======================================================

class Crop(models.Model):
    name = models.CharField(max_length=120, unique=True)
    scientific_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Nombre científico (ej. Solanum lycopersicum)"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción general del cultivo (origen, características, etc.)"
    )

    season = models.CharField(
        max_length=120,
        blank=True,
        help_text="Época o ciclo de siembra recomendado"
    )
    soil_type = models.CharField(
        max_length=120,
        blank=True,
        help_text="Tipo de suelo óptimo (franco, franco-arenoso, etc.)"
    )
    climate = models.CharField(
        max_length=120,
        blank=True,
        help_text="Clima ideal (temperatura, altitud, etc.)"
    )

    water_requirement = models.CharField(
        max_length=150,
        blank=True,
        help_text="Requerimiento general de agua (bajo, medio, alto)"
    )
    general_irrigation_notes = models.TextField(
        blank=True,
        help_text="Notas generales de riego si no hay guía específica."
    )
    general_fertilization_notes = models.TextField(
        blank=True,
        help_text="Notas generales de fertilización para este cultivo."
    )

    spacing_between_plants_cm = models.FloatField(
        null=True, blank=True,
        help_text="Distancia entre plantas (cm)"
    )
    spacing_between_rows_cm = models.FloatField(
        null=True, blank=True,
        help_text="Distancia entre surcos/filas (cm)"
    )

    def __str__(self):
        return self.name


# ======================================================
# 2️⃣ Enfermedades y plagas
# ======================================================

class Disease(models.Model):
    DISEASE_TYPES = [
        ('plaga', 'Plaga'),
        ('fungica', 'Fúngica'),
        ('bacteriana', 'Bacteriana'),
        ('viral', 'Viral'),
        ('fisiologica', 'Fisiológica'),
        ('otra', 'Otra'),
    ]

    name = models.CharField(max_length=100)
    ml_label = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Etiqueta exacta usada por el modelo ML (ej: tomate_mosca_blanca)"
    )
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='diseases')
    disease_type = models.CharField(max_length=50, choices=DISEASE_TYPES, default='plaga')

    description = models.TextField(
        help_text="Descripción general de la enfermedad o plaga."
    )
    symptoms = models.TextField(
        help_text="Síntomas típicos observables en el cultivo."
    )

    # Campos técnicos extra
    causal_agent = models.CharField(
        max_length=150,
        blank=True,
        help_text="Agente causal (hongo, bacteria, insecto específico, etc.)"
    )
    transmission = models.TextField(
        blank=True,
        help_text="Formas de transmisión / condiciones predisponentes."
    )

    control_cultural = models.TextField(
        blank=True,
        help_text="Medidas culturales (rotación, manejo de rastrojos, densidad, etc.)"
    )
    control_biological = models.TextField(
        blank=True,
        help_text="Control biológico (parasitoides, hongos entomopatógenos, etc.)"
    )
    control_chemical = models.TextField(
        blank=True,
        help_text="Recomendaciones químicas generales (SIN marcas comerciales)."
    )

    recommendations = models.TextField(
        help_text="Resumen de manejo integrado recomendado."
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["crop", "disease_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.crop.name})"


class DiseaseImage(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='disease_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


# ======================================================
# 3️⃣ Riego (Guía técnica)
# ======================================================

class IrrigationGuide(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name="irrigation_guides")
    region = models.ForeignKey(
        Region,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="irrigation_guides"
    )
    stage = models.CharField(
        max_length=32,
        choices=PhenologicalStage.choices,
        help_text="Etapa fenológica"
    )
    system = models.CharField(
        max_length=32,
        choices=IrrigationSystem.choices,
        help_text="Sistema de riego"
    )

    frequency_days = models.FloatField(
        null=True, blank=True,
        help_text="Frecuencia de riego (días entre riegos)"
    )
    volume_l_m2 = models.FloatField(
        null=True, blank=True,
        help_text="Litros de agua por m² en cada riego (aprox.)"
    )
    duration_minutes = models.FloatField(
        null=True, blank=True,
        help_text="Duración de riego (minutos) si aplica (goteo/aspersión)."
    )

    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales (tipo de suelo, clima, ajustes, etc.)"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("crop", "region", "stage", "system")
        ordering = ["crop", "region", "stage"]

    def __str__(self):
        r = f" - {self.region.name}" if self.region else ""
        return f"Riego {self.crop.name}{r} - {self.get_stage_display()} ({self.get_system_display()})"


# ======================================================
# 4️⃣ Fertilización (Plan y entradas)
# ======================================================

class FertilizationPlan(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name="fertilization_plans")
    region = models.ForeignKey(
        Region,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="fertilization_plans"
    )
    name = models.CharField(max_length=150, help_text="Nombre del plan (ej. Plan estándar tomate tecnificado)")
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["crop", "name"]

    def __str__(self):
        r = f" - {self.region.name}" if self.region else ""
        return f"Plan fert. {self.crop.name}{r} - {self.name}"


class FertilizationEntry(models.Model):
    plan = models.ForeignKey(FertilizationPlan, on_delete=models.CASCADE, related_name="entries")
    stage = models.CharField(
        max_length=32,
        choices=PhenologicalStage.choices,
        help_text="Etapa fenológica a la que aplica"
    )

    npk_ratio = models.CharField(
        max_length=50,
        blank=True,
        help_text="Relación recomendada N-P-K (ej. 15-15-15, 10-30-10)"
    )
    source = models.CharField(
        max_length=150,
        blank=True,
        help_text="Tipo de fertilizante (ej. Urea, DAP, 15-15-15, etc.)"
    )
    dose_kg_ha = models.FloatField(
        null=True, blank=True,
        help_text="Dosis aproximada (kg/ha)"
    )
    applications = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Número de aplicaciones en esta etapa."
    )
    interval_days = models.FloatField(
        null=True, blank=True,
        help_text="Intervalo entre aplicaciones (días)."
    )

    notes = models.TextField(
        blank=True,
        help_text="Notas específicas (fraccionamiento, mezclas, precauciones)."
    )

    class Meta:
        ordering = ["plan", "stage"]

    def __str__(self):
        return f"{self.plan} - {self.get_stage_display()}"


# ======================================================
# 5️⃣ Producción y prácticas de manejo
# ======================================================

class CropProduction(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='production_data')
    region = models.ForeignKey(
        Region,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="production_data"
    )
    average_yield = models.FloatField(
        help_text="Rendimiento promedio (toneladas/hectárea)"
    )
    practices = models.TextField(
        help_text="Prácticas comunes de producción (riego, poda, densidad de siembra, etc.)"
    )
    cost_estimate = models.FloatField(
        help_text="Costo estimado de producción por hectárea",
        null=True, blank=True
    )
    market_price = models.FloatField(
        help_text="Precio promedio de venta por tonelada",
        null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        r = f" - {self.region.name}" if self.region else ""
        return f"Producción de {self.crop.name}{r}"


class CropPractice(models.Model):
    """
    Buenas prácticas específicas por cultivo y etapa (poda, deshoje, tutorado, etc.).
    """
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name="practices")
    stage = models.CharField(
        max_length=32,
        choices=PhenologicalStage.choices,
        blank=True
    )
    name = models.CharField(max_length=150, help_text="Nombre de la práctica (ej. Poda de formación).")
    description = models.TextField(help_text="Descripción general de la práctica.")
    step_by_step = models.TextField(
        blank=True,
        help_text="Pasos recomendados (puedes usar viñetas con saltos de línea)."
    )
    safety_notes = models.TextField(
        blank=True,
        help_text="Consideraciones de seguridad y cuidado."
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        stage = f" - {self.get_stage_display()}" if self.stage else ""
        return f"{self.crop.name}{stage}: {self.name}"


# ======================================================
# 6️⃣ Herramientas y equipos agrícolas
# ======================================================

class Tool(models.Model):
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        related_name='tools',
        null=True, blank=True,
        help_text="Opcional: herramienta asociada a un cultivo concreto."
    )
    name = models.CharField(max_length=150)
    description = models.TextField(help_text="Descripción y uso de la herramienta")
    purpose = models.CharField(
        max_length=150,
        help_text="Propósito principal (siembra, poda, cosecha, riego, etc.)"
    )
    recommended_stage = models.CharField(
        max_length=120,
        blank=True,
        help_text="Etapa del cultivo donde se recomienda (si aplica)"
    )
    safety_notes = models.TextField(
        blank=True,
        help_text="Recomendaciones de seguridad al usarla."
    )

    def __str__(self):
        return f"{self.name} ({self.crop.name})" if self.crop else self.name


# ======================================================
# 7️⃣ Artículos de conocimiento (para el chat)
# ======================================================

class KnowledgeArticle(models.Model):
    class Category(models.TextChoices):
        FERTILIZATION = "fertilizacion", "Fertilización"
        TOOLS = "herramientas", "Herramientas"
        TECHNIQUE = "tecnicas", "Técnicas de producción"
        MANAGEMENT = "manejo", "Manejo/Buenas prácticas"
        PESTS = "plagas", "Plagas y enfermedades"
        OTHER = "otros", "Otros"

    class Subtopic(models.TextChoices):
        IRRIGATION = "riego", "Riego"
        FERTILIZATION_PLAN = "plan_fertilizacion", "Plan de fertilización"
        PRUNING = "poda", "Poda"
        HARVEST = "cosecha", "Cosecha"
        SOIL = "suelo", "Manejo de suelo"
        TOOLS_USE = "uso_herramientas", "Uso de herramientas"
        PEST_CONTROL = "control_plagas", "Control de plagas"
        GENERAL = "general", "General"

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=32, choices=Category.choices, db_index=True)
    subtopic = models.CharField(
        max_length=32,
        choices=Subtopic.choices,
        blank=True,
        help_text="Tema más específico (riego, poda, fertilización, etc.)"
    )
    crop = models.ForeignKey("Crop", null=True, blank=True, on_delete=models.SET_NULL)
    disease = models.ForeignKey(
        Disease,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Opcional: artículo asociado a una enfermedad/plaga concreta."
    )
    tool = models.ForeignKey(
        Tool,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Opcional: artículo asociado a una herramienta específica."
    )

    # ⚠️ NUEVO: para hacer match más preciso con preguntas
    specific_question = models.CharField(
        max_length=300,
        blank=True,
        help_text="Pregunta típica que responde este artículo (ej. '¿cómo regar tomate en floración?')."
    )
    difficulty = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("basico", "Básico"),
            ("intermedio", "Intermedio"),
            ("avanzado", "Avanzado"),
        ],
        help_text="Nivel técnico del contenido."
    )

    tags = models.CharField(max_length=250, blank=True)
    summary = models.CharField(
        max_length=300,
        blank=True,
        help_text="Resumen corto para mostrar en el chat."
    )
    key_points = models.TextField(
        blank=True,
        help_text="Puntos clave (pueden ser viñetas separadas por saltos de línea)."
    )
    content = models.TextField(help_text="Contenido completo del artículo.")
    tools_text = models.TextField(
        blank=True,
        help_text="Texto libre de herramientas mencionadas (si aplica)."
    )
    sources = models.TextField(blank=True)

    is_published = models.BooleanField(default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "is_published"]),
            models.Index(fields=["crop", "category"]),
        ]
        ordering = ["-updated_at", "title"]

    def __str__(self):
        crop_name = f" ({self.crop})" if self.crop else ""
        return f"{self.title}{crop_name} - {self.get_category_display()}"


# ======================================================
# 8️⃣ Imágenes subidas por el usuario (análisis IA)
# ======================================================

class UploadedImage(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    image = models.ImageField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)
    predicted_disease = models.ForeignKey(Disease, null=True, blank=True, on_delete=models.SET_NULL)
    confidence = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Imagen subida por {self.user} - {self.created_at.strftime('%Y-%m-%d')}"


# ======================================================
# 9️⃣ Chat del usuario
# ======================================================

class ChatMessage(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    message = models.TextField()
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    attached_image = models.ForeignKey(UploadedImage, null=True, blank=True, on_delete=models.SET_NULL)

    # Opcional: detectar y guardar contexto técnico
    detected_crop = models.ForeignKey(
        Crop,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_messages"
    )
    detected_stage = models.CharField(
        max_length=32,
        choices=PhenologicalStage.choices,
        blank=True
    )
    detected_intent = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ej. riego, fertilizacion, plagas, herramientas..."
    )

    def __str__(self):
        return f"Mensaje de {self.user} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    
class FAQ(models.Model):
    class Topic(models.TextChoices):
        RIEGO = "riego", "Riego"
        FERTILIZACION = "fertilizacion", "Fertilización"
        PLAGAS = "plagas", "Plagas"
        HERRAMIENTAS = "herramientas", "Herramientas"
        SIEMBRA = "siembra", "Densidad / Siembra"
        MANEJO = "manejo", "Manejo / Producción"
        GENERAL = "general", "General"

    crop = models.ForeignKey(
        Crop,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Cultivo al que aplica (opcional para preguntas generales)."
    )
    topic = models.CharField(
        max_length=30,
        choices=Topic.choices
    )
    question = models.CharField(
        max_length=300,
        help_text="Pregunta típica del productor (tal como la haría)."
    )
    answer = models.TextField(
        help_text="Respuesta técnica y clara para mostrar en el chat."
    )
    keywords = models.CharField(
        max_length=300,
        blank=True,
        help_text="Palabras clave separadas por coma (distancia, densidad, marco, etc.)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["crop", "topic", "-updated_at"]

    def __str__(self):
        crop_name = f" - {self.crop.name}" if self.crop else ""
        return f"{self.get_topic_display()}{crop_name}: {self.question[:40]}..."

