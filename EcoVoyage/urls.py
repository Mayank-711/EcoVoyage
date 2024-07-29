"""
URL configuration for EcoVoyage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from authapp import views as aviews
from mainapp import views as mviews

urlpatterns = [
    path('admin/', admin.site.urls),
]

authappurl = [
    path('', aviews.landingpage, name="landingpage"),
    path('home/', aviews.landingpage, name='home'),
    path('login/', aviews.loginpage, name='login'), 
    path('signup/', aviews.signuppage, name="signup"),
    path('changepass/', aviews.changepass, name="changepass"),
    path('view_profile/<int:user_id>/', aviews.view_profile, name='view_profile'),
    path('edit_profile/<int:user_id>/', aviews.edit_profile, name='edit_profile'),
    path('logout/', aviews.user_logout, name='logout'),
]

mainappurl = [
    path('mappage/', mviews.mappage, name='mappage'),
]

urlpatterns = urlpatterns + authappurl + mainappurl
