from rest_framework import serializers

from .models import User

class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'role','phone','username','password','first_name','last_name','email'
        ]
        