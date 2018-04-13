from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('purchaser/', views.purchaser, name='purchaser'),
    path('facility/', views.facility, name='facility'),
    path('sendPackage/<str:shipmentID>/', views.send_package, name='send_package'),
    path('SendShipment/', views.SendShipment, name='SendShipment'),
    path('ReceiveShipment/<str:shipmentID>/', views.ReceiveShipment, name='ReceiveShipment'),
    path('OutForDelivery/<str:shipmentID>/', views.OutForDelivery, name='OutForDelivery'),
    path('DeliverShipment/<str:shipmentID>/', views.DeliverShipment, name='DeliverShipment'),
    path('vendor/', views.vendor, name='vendor'),
    path('signOut/', views.signOut, name='signOut'),
]