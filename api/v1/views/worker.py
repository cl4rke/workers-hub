import json
from django.http import JsonResponse
from workers_hub.decorators import worker_api_confirmation
from workers_hub.exceptions import MissingArgumentsException
from workers_hub.models import Proposal
from workers_hub.models import Request


@worker_api_confirmation
def proposal(req, request_id):
    if req.method == 'POST':
        try:
            data = json.loads(req.body)
        except ValueError:
            data = req.POST

        if 'message' not in data:
            raise MissingArgumentsException('message')
        if 'cost' not in data:
            raise MissingArgumentsException('cost')

        worker = req.worker
        request = Request.objects.get(id=request_id)

        proposal = Proposal(cost=data['cost'], message=data['message'], worker=worker, status=Proposal.OPEN,
                            request=request)

        proposal.save()

        return JsonResponse({
            'status': 'success',
            'message': proposal.worker.user.username,
        })
    elif req.method == 'DELETE':
        proposal = Proposal.objects.get(id=request_id)
        if proposal.status == Proposal.OPEN:
            proposal.delete()

            return JsonResponse({
                'status': 'success',
                'message': proposal.request.subject,
            })
        else:
            response = JsonResponse({
                'status': 'error',
                'message': 'Only OPEN bids can be cancelled.',
            })
            response.status_code = 404
            return response

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.',
    })


@worker_api_confirmation
def requests(req):
    worker = req.worker

    professions = worker.profession_set

    available_requests = []

    for request in Request.objects.all():
        available = True

        for profession in request.professions.all():
            if not professions.filter(name=profession.name).exists():
                available = False
                break

        if available:
            available_requests.append(request)

    return JsonResponse({
        'status': 'success',
        'message': [
            {
                'subject': request.subject,
                'description': request.description,
                'range_min': request.range_min,
                'range_max': request.range_max,
                'tags': [profession.name for profession in request.professions.all()],
                'images': [image.url for image in request.image_set.all()],
                'status': request.status,
            }
            for request in available_requests
        ],
    })


@worker_api_confirmation
def proposals(req):
    worker = req.worker

    return JsonResponse({
        'status': 'success',
        'message': [
            {
                'request': {
                    'subject': proposal.request.subject,
                    'description': proposal.request.description,
                    'range_min': proposal.request.range_min,
                    'range_max': proposal.request.range_max,
                    'tags': [profession.name for profession in proposal.request.professions.all()],
                    'images': [image.url for image in proposal.request.image_set.all()],
                    'status': proposal.request.status,
                },
                'cost': proposal.cost,
                'message': proposal.message,
                'status': proposal.status,
            }
            for proposal in worker.proposal_set.all()
        ],
    })
