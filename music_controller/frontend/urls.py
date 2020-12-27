from django.urls import path
from .views import index

# helps django to know that this urls.py file belogns to frontend app
# helps to redirect from other apps
app_name = 'frontend'

urlpatterns = [
    # name give a formal name, so when we redirect we know where to
    path('', index, name=''),
    path('join', index),
    path('create', index),
    path('room/<str:roomCode>', index)
]
