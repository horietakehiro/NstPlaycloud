from django import forms

from playground.models import Image
from playground import messages


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']
        labels = {
            'image' : 'UploadImage'
        }

    def is_valid(self):
        """
        This returns a tuple.
        (bool : validation result, str : message)
        """
        is_valid = super(ImageForm, self).is_valid()
        name = self.files["image"].name
        if not is_valid:
            return False, messages.UPLOAD_FAIL_INVALID.format(name)

        # check duplication
        obj = Image.objects.filter(image__endswith=name)
        if len(obj):
            return False, messages.UPLOAD_FAIL_DUPLICATED.format(name)


        return True, messages.UPLOAD_SUCCESS.format(name)


    def save(self):
        """
        if save succeeded, return image object
        if save failed(due to s3 error), return None
        """
        try:
            res = super(ImageForm, self).save()
        except:
            return None
        return res


class TransferForm(forms.Form):
    
    content = forms.ChoiceField(label='Content', choices=[])
    style = forms.ChoiceField(label='Style', choices=[])

    def __init__(self, *args, image_list=None, **kwargs):
        super(TransferForm, self).__init__(*args, **kwargs)

        if image_list is None:
            image_list = Image.objects.all()
        
        choices = [(str(image.id), image.basename) for image in image_list]
        self.fields['content'].choices = choices
        self.fields['style'].choices = choices
