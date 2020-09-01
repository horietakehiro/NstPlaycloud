from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.decorators import login_required


from playground.models import Image, Result
from playground.forms import ImageForm, TransferForm
from playground import messages as playground_messages


# diverse django's default admin site for login authentication
login = login_required(login_url="/admin/login/")

# Create your views here.
@login
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

@login
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


@login
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
    delete_message = playground_messages.DELETE_QUEUE_MESSAGE
    delete_message["request_body"]["basenames"] = [image.basename]
    msg = image.send_delete_message(delete_message)
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

@login
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
    transfer_message = playground_messages.TRANSFER_QUEUE_MESSAGE
    transfer_message["request_body"]["content_list"] = [result.content.basename]
    transfer_message["request_body"]["style_list"] = [result.style.basename]
    transfer_message["request_body"]["transfer_list"] = [result.transfer.basename]

    msg = result.send_transfer_message(transfer_message)
    if msg is not None:
        messages.add_message(request, messages.WARNING, msg)

    return redirect("image_list")



@login
def result_list(request, image_id=0):
    if request.method != "GET":
        return HttpResponse(status=405)

    # by defailt, get all result list
    if image_id == 0:
        result_list = Result.objects.all()
    else:
        result_list = Result.objects.filter(
            Q(content_id=image_id) | Q(style_id=image_id) | Q(transfer_id=image_id)
        )

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