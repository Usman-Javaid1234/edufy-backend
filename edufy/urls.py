from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Edufy Administration"
admin.site.site_title  = "Edufy Admin"
admin.site.index_title = "Welcome to Edufy Admin Panel"

urlpatterns = [
    path("admin/",           admin.site.urls),
    path("api/auth/",        include("accounts.urls")),
    path("api/courses/",     include("courses.urls")),
    path("api/assignments/", include("assignments.urls")),
    path("api/grading/",     include("grading.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
