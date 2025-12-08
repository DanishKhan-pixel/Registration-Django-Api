from django.db.models import Q
from datetime import datetime, timedelta
from authentication.models import User
from organization.models import Organization


def get_calculated_data(model, request):
    """
    Get filtered data from any model with dynamic filters and date ranges.

    Args:
        model: Django model class
        request: Django request object to get query parameters

    Returns:
        Filtered queryset
    """

    try:
        # Get query parameters
        query_params = request.query_params
        org_id = query_params.get('org_id')
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')

        # Base queryset
        queryset = model.objects.filter(is_deleted=False)

        # Apply organization filter if org_id is provided
        if org_id:
            if model == User:
                queryset = queryset.filter(profile__organization_id=org_id)
            elif model == Organization:
                queryset = queryset.filter(id=org_id)

        # Apply date range filter if provided
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        elif start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        elif end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # Calculate percentage difference if date range is provided
        if start_date and end_date:
            # Convert string dates to datetime objects
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Calculate the duration in days
            duration = (end - start).days
            
            # Calculate previous period dates
            prev_start = start - timedelta(days=duration)
            prev_end = start - timedelta(days=1)
            
            # Get current period count
            current_count = queryset.count()
            
            # Get previous period count
            previous_count = model.objects.filter(
                is_deleted=False,
                created_at__range=[prev_start, prev_end]
            ).count()
            
            # Calculate percentage difference
            if previous_count > 0:
                percentage_difference = ((current_count - previous_count) / previous_count) * 100
            else:
                # If previous count is 0, set difference to 100% if current count is positive
                percentage_difference = 100 if current_count > 0 else 0

            # Add percentage_difference to request object with model-specific key
            model_key = 'organization_percentage' if model == Organization else 'user_percentage'
            setattr(request, model_key, round(percentage_difference, 2))

        return queryset
    except Exception as e:
        raise e

