from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter

from student_management.custom.custom_response import CustomResponse


class ServiceViewMixin:
    """Resolve the view's ``service_class`` into an instance per request."""

    service_class: "type | None" = None
    entity_name: str = "Resource"

    def get_service(self):
        service_class = self.service_class
        if service_class is None:
            raise NotImplementedError(f"{type(self).__name__} must define `service_class`.")
        return service_class()

    def get_acting_user(self):
        """The authenticated user driving the request, or ``None`` if anonymous.

        Threaded into the service so the repository can stamp ``created_by`` /
        ``updated_by`` (an ``AnonymousUser`` is never a valid FK, hence ``None``)."""
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        return user if getattr(user, "is_authenticated", False) else None


class BaseListCreateView(ServiceViewMixin, generics.ListCreateAPIView):
    """Generic GET (paginated list) + POST (create) wrapped in CustomResponse.

    A new module only needs::

        class TeacherView(BaseListCreateView):
            permission_classes = [IsAuthenticated]
            serializer_class = TeacherSerializer
            service_class = TeacherService
            entity_name = "Teacher"
            filterset_fields = ["department"]      # ?department=3
            search_fields = ["name", "email"]      # ?search=...
            ordering_fields = ["name", "id"]       # ?ordering=-name

    The filter backends are always enabled; a module gets filtering only for the
    fields it declares (no declaration => behaves as a plain list).
    """

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        return self.get_service().list()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return CustomResponse(
                data=self.get_paginated_response(serializer.data).data,
                message=f"{self.entity_name} fetched successfully",
                status=status.HTTP_200_OK,
            )
        serializer = self.get_serializer(queryset, many=True)
        return CustomResponse(
            data={"count": queryset.count(), "results": serializer.data},
            message=f"{self.entity_name} fetched successfully",
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_service().create(serializer.validated_data, user=self.get_acting_user())
        return CustomResponse(
            data=self.get_serializer(instance).data,
            message=f"{self.entity_name} created successfully",
            status=status.HTTP_201_CREATED,
        )


class BaseRetrieveUpdateDestroyView(ServiceViewMixin, generics.RetrieveUpdateDestroyAPIView):
    """Generic GET (detail) + PUT/PATCH (update) + DELETE wrapped in CustomResponse."""

    def get_queryset(self):
        return self.get_service().get_all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return CustomResponse(
            data=serializer.data,
            message=f"{self.entity_name} details fetched successfully",
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = self.get_service().update(
            instance, serializer.validated_data, user=self.get_acting_user()
        )
        return CustomResponse(
            data=self.get_serializer(updated).data,
            message=f"{self.entity_name} updated successfully",
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.get_service().delete(instance, user=self.get_acting_user())
        return CustomResponse(
            message=f"{self.entity_name} deleted successfully",
            status=status.HTTP_204_NO_CONTENT,
        )
