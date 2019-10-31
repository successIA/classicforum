from forum.image_app.models import Image

def delete_unticked_images(instance, form):
    if instance.images:
        '''
        Image delete should occur only if the instance has an images attribute
        '''
        for image_obj in instance.images.all():
            '''
            Remove all the unticked images from the database by checking if the
            key of the form's image_url coming through is False
            '''
            if form.cleaned_data.get(image_obj.image.url) == 'False':
                # If false get the image form the Image table through its pk
                img = Image.objects.get(pk=image_obj.pk)
                # delete the image from the file system
                img.image.delete()
                # delete image from the image table
                img.delete()


def save_chosen_images(view_instance, instance):
    '''

    '''
    self = view_instance
    for i in range(1, 6):
        image_set = 'image_set' + str(i)
        if self.request.FILES.getlist(image_set):
            for image in self.request.FILES.getlist(image_set):
                Image.objects.create(content_object=instance, image=image)

def my_function(instance):
    return 'bread'

