from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.conf import settings

from playground.models import Image, Result
from playground.forms import ImageForm, TransferForm
from playground import messages as playground_messages

# Create your views here.
def image_list(request):
    if request.method != "GET":
        return HttpResponse(status=405)
        
    image_list = Image.objects.all()

    image_form = ImageForm()
    transfer_form = TransferForm(image_list=image_list)
    
    return render(
        request,
        "playground/image_list.html",
        {
            "image_list" : image_list,
            "image_form" : image_form,
            "transfer_form" : transfer_form,
        },
    )


def upload(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    form = ImageForm(request.POST, request.FILES)
    is_valid, msg = form.is_valid()
    if not is_valid:
        messages.add_message(request, messages.ERROR, msg)
        return redirect("image_list")


    image = form.save()
    if image is None:
        messages.add_message(request, messages.ERROR, playground_messages.UPLOAD_FAIL_S3ERROR)
    else:
        messages.add_message(request, messages.INFO, msg)
    return redirect("image_list")


def delete(request, image_id):
    # only accept post method
    if request.method != "POST":
        messages.add_message(
            request,
            messages.ERROR,
            playground_messages.DELETE_FAIL_INVALID_METHOD,
        )
        return redirect("image_list")
    
    # check the image certainly exists
    try:
        image = Image.objects.get(id=int(image_id))
    except Image.DoesNotExist:
        messages.add_message(
            request,
            messages.ERROR,
            playground_messages.DELETE_FAIL_NOTEXISTS.format(image_id)
        )
        return redirect("image_list")

    # send sqs queue a request message for deleting image files in s3
    msg = image.send_delete_message()
    if msg is not None:
        messages.add_message(
            request,
            messages.WARNING,
            msg
        )

    # even if message sending fails, continue to delete image data in database.
    image_name = image.basename
    res = image.delete()
    messages.add_message(
        request,
        messages.INFO, 
        playground_messages.DELETE_SUCCESS.format(image_name)
    )

    return redirect("image_list")

def transfer(request):
    if request.method != "POST":
        messages.add_message(
            request,
            messages.ERROR,
            playground_messages.TRANSFER_FAIL_INVALID_METHOD,
        )
        return redirect("image_list")

    form = TransferForm(request.POST)
    if not form.is_valid():
        messages.add_message(
            request,
            messages.ERROR,
            playground_messages.TRANSFER_FAIL_INVALID,
        )
        return redirect("image_list")


    transfer, msg = Image.create_transfer_image(
        content_id=form.cleaned_data["content"],
        style_id=form.cleaned_data["style"],
    )

    messages.add_message(request, messages.INFO, msg)

    result = Result.objects.create(
        transfer_id=transfer.id,
        content_id=form.cleaned_data["content"],
        style_id=form.cleaned_data["style"],
    )

    msg = result.send_transfer_message()
    if msg is not None:
        messages.add_message(request, messages.WARNING, msg)

    return redirect("image_list")




def result_list(request):
    if request.method != "GET":
        return HttpResponse(status=405)

    result_list = Result.objects.all()

    image_form = ImageForm()
    transfer_form = TransferForm()

    
    return render(
        request,
        "playground/result_list.html",
        {
            "result_list" : result_list,
            "image_form" : image_form,
            "transfer_form" : transfer_form,
        },
    )