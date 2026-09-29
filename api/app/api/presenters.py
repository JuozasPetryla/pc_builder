"""Convert ORM entities to API representations with navigable API links."""

from app.models.domain import Build, Component, RetailOffer, Review
from app.schemas.build import BuildLinks, BuildRead
from app.schemas.component import ComponentLinks, ComponentRead, OfferLinks, OfferRead
from app.schemas.review import ReviewLinks, ReviewRead


def offer_to_read(offer: RetailOffer, build_id: int) -> OfferRead:
    component_url = f"/api/v1/components/{offer.component_id}"
    return OfferRead(
        id=offer.id,
        component_id=offer.component_id,
        retailer=offer.retailer,
        price=offer.price,
        product_url=offer.product_url,
        in_stock=offer.in_stock,
        links=OfferLinks(
            self=f"/api/v1/offers/{offer.id}",
            component=component_url,
            build=f"/api/v1/builds/{build_id}",
        ),
    )


def component_to_read(component: Component) -> ComponentRead:
    return ComponentRead(
        id=component.id,
        build_id=component.build_id,
        category=component.category,
        manufacturer=component.manufacturer,
        model=component.model,
        description=component.description,
        specifications=component.specifications,
        offers=[offer_to_read(offer, component.build_id) for offer in component.offers],
        created_at=component.created_at,
        updated_at=component.updated_at,
        links=ComponentLinks(
            self=f"/api/v1/components/{component.id}",
            build=f"/api/v1/builds/{component.build_id}",
            offers=f"/api/v1/builds/{component.build_id}/components/{component.id}/offers",
        ),
    )


def review_to_read(review: Review) -> ReviewRead:
    return ReviewRead(
        id=review.id,
        build_id=review.build_id,
        author_id=review.author_id,
        author_name=review.author_name,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        links=ReviewLinks(
            self=f"/api/v1/reviews/{review.id}",
            build=f"/api/v1/builds/{review.build_id}",
        ),
    )


def build_to_read(build: Build) -> BuildRead:
    return BuildRead(
        id=build.id,
        name=build.name,
        owner_id=build.owner_id,
        owner_name=build.owner_name,
        description=build.description,
        is_public=build.is_public,
        components=[component_to_read(component) for component in build.components],
        reviews=[review_to_read(review) for review in build.reviews],
        created_at=build.created_at,
        updated_at=build.updated_at,
        links=BuildLinks(
            self=f"/api/v1/builds/{build.id}",
            components=f"/api/v1/builds/{build.id}/components",
            reviews=f"/api/v1/builds/{build.id}/reviews",
        ),
    )
