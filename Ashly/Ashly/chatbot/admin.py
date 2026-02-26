from django.contrib import admin
from .models import (
    Region,
    Crop,
    Disease,
    DiseaseImage,
    IrrigationGuide,
    FertilizationPlan,
    FertilizationEntry,
    CropProduction,
    CropPractice,
    Tool,
    KnowledgeArticle,
    UploadedImage,
    ChatMessage,
)


# ==========================
# INLINES
# ==========================

class DiseaseImageInline(admin.TabularInline):
    model = DiseaseImage
    extra = 1


class IrrigationGuideInline(admin.TabularInline):
    model = IrrigationGuide
    extra = 1
    fields = (
        "region",
        "stage",
        "system",
        "frequency_days",
        "volume_l_m2",
        "duration_minutes",
    )


class FertilizationEntryInline(admin.TabularInline):
    model = FertilizationEntry
    extra = 1
    fields = (
        "stage",
        "npk_ratio",
        "source",
        "dose_kg_ha",
        "applications",
        "interval_days",
    )


class CropPracticeInline(admin.TabularInline):
    model = CropPractice
    extra = 1
    fields = ("stage", "name", "description")


# ==========================
# REGION
# ==========================

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ==========================
# CROP
# ==========================

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "scientific_name",
        "climate",
        "season",
        "water_requirement",
    )
    search_fields = (
        "name",
        "scientific_name",
        "description",
        "climate",
        "soil_type",
    )
    list_filter = ("climate", "water_requirement")
    inlines = [IrrigationGuideInline, CropPracticeInline]


# ==========================
# DISEASE
# ==========================

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ("name", "crop", "disease_type", "updated_at")
    list_filter = ("crop", "disease_type")
    search_fields = (
        "name",
        "crop__name",
        "description",
        "symptoms",
        "causal_agent",
    )
    readonly_fields = ("updated_at",)
    inlines = [DiseaseImageInline]


@admin.register(DiseaseImage)
class DiseaseImageAdmin(admin.ModelAdmin):
    list_display = ("disease", "uploaded_at")
    readonly_fields = ("uploaded_at",)


# ==========================
# IRRIGATION
# ==========================

@admin.register(IrrigationGuide)
class IrrigationGuideAdmin(admin.ModelAdmin):
    list_display = (
        "crop",
        "region",
        "stage",
        "system",
        "frequency_days",
        "volume_l_m2",
    )
    list_filter = ("crop", "region", "stage", "system")
    search_fields = ("crop__name", "region__name", "notes")
    readonly_fields = ("updated_at",)


# ==========================
# FERTILIZATION
# ==========================

@admin.register(FertilizationPlan)
class FertilizationPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "crop", "region", "updated_at")
    list_filter = ("crop", "region")
    search_fields = ("name", "crop__name", "region__name", "description")
    readonly_fields = ("updated_at",)
    inlines = [FertilizationEntryInline]


@admin.register(FertilizationEntry)
class FertilizationEntryAdmin(admin.ModelAdmin):
    list_display = (
        "plan",
        "stage",
        "npk_ratio",
        "dose_kg_ha",
        "applications",
        "interval_days",
    )
    list_filter = ("plan", "stage")
    search_fields = ("plan__name", "plan__crop__name", "npk_ratio", "source")


# ==========================
# PRODUCTION & PRACTICES
# ==========================

@admin.register(CropProduction)
class CropProductionAdmin(admin.ModelAdmin):
    list_display = ("crop", "region", "average_yield", "market_price", "updated_at")
    list_filter = ("crop", "region")
    search_fields = ("crop__name", "region__name", "practices")
    readonly_fields = ("updated_at",)


@admin.register(CropPractice)
class CropPracticeAdmin(admin.ModelAdmin):
    list_display = ("crop", "stage", "name", "updated_at")
    list_filter = ("crop", "stage")
    search_fields = ("crop__name", "name", "description")
    readonly_fields = ("updated_at",)


# ==========================
# TOOLS
# ==========================

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ("name", "crop", "purpose", "recommended_stage")
    list_filter = ("crop", "purpose")
    search_fields = ("name", "description", "purpose", "crop__name")


# ==========================
# KNOWLEDGE ARTICLES
# ==========================

@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "subtopic",
        "crop",
        "disease",
        "tool",
        "is_published",
        "updated_at",
    )
    list_filter = (
        "category",
        "subtopic",
        "is_published",
        "crop",
        "disease",
        "tool",
    )
    search_fields = (
        "title",
        "summary",
        "tags",
        "content",
        "key_points",
        "crop__name",
        "disease__name",
        "tool__name",
    )
    autocomplete_fields = ("crop", "disease", "tool")
    readonly_fields = ("updated_at",)


# ==========================
# UPLOADED IMAGES
# ==========================

@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ("user", "predicted_disease", "confidence", "created_at")
    list_filter = ("predicted_disease", "created_at")
    search_fields = ("user__username", "predicted_disease__name")
    readonly_fields = ("created_at",)


# ==========================
# CHAT MESSAGES
# ==========================

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "created_at",
        "detected_crop",
        "detected_stage",
        "detected_intent",
    )
    list_filter = ("detected_crop", "detected_stage", "detected_intent")
    search_fields = ("user__username", "message", "response")
    readonly_fields = ("created_at",)
