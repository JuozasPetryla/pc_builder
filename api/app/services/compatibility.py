from decimal import Decimal
from typing import Any

from app.models.domain import Build, Component, ComponentCategory
from app.schemas.build import CompatibilityIssue, CompatibilityRead

REQUIRED_BUILD_CATEGORIES = {
    ComponentCategory.CPU,
    ComponentCategory.MOTHERBOARD,
    ComponentCategory.MEMORY,
    ComponentCategory.STORAGE,
    ComponentCategory.PSU,
    ComponentCategory.CASE,
}


def _spec(component: Component, name: str) -> Any:
    return component.specifications.get(name)


def evaluate_build(build: Build) -> CompatibilityRead:
    by_category = {ComponentCategory(item.category): item for item in build.components}
    missing = sorted(category.value for category in REQUIRED_BUILD_CATEGORIES - by_category.keys())
    issues: list[CompatibilityIssue] = []

    cpu = by_category.get(ComponentCategory.CPU)
    motherboard = by_category.get(ComponentCategory.MOTHERBOARD)
    memory = by_category.get(ComponentCategory.MEMORY)
    gpu = by_category.get(ComponentCategory.GPU)
    psu = by_category.get(ComponentCategory.PSU)
    case = by_category.get(ComponentCategory.CASE)
    cooler = by_category.get(ComponentCategory.COOLER)

    if cpu and motherboard and _spec(cpu, "socket") != _spec(motherboard, "socket"):
        issues.append(
            CompatibilityIssue(
                code="CPU_SOCKET_MISMATCH",
                message="Procesoriaus ir pagrindinės plokštės lizdai nesutampa.",
                component_ids=[cpu.id, motherboard.id],
            )
        )

    if motherboard and memory and _spec(motherboard, "memory_type") != _spec(memory, "memory_type"):
        issues.append(
            CompatibilityIssue(
                code="MEMORY_TYPE_MISMATCH",
                message="Atminties tipas nėra palaikomas pagrindinės plokštės.",
                component_ids=[motherboard.id, memory.id],
            )
        )

    if motherboard and case:
        supported = _spec(case, "supported_form_factors") or []
        if _spec(motherboard, "form_factor") not in supported:
            issues.append(
                CompatibilityIssue(
                    code="MOTHERBOARD_CASE_MISMATCH",
                    message="Korpusas nepalaiko pagrindinės plokštės formato.",
                    component_ids=[motherboard.id, case.id],
                )
            )

    if gpu and case and int(_spec(gpu, "length_mm")) > int(_spec(case, "max_gpu_length_mm")):
        issues.append(
            CompatibilityIssue(
                code="GPU_TOO_LONG",
                message="Vaizdo plokštė yra per ilga pasirinktam korpusui.",
                component_ids=[gpu.id, case.id],
            )
        )

    if gpu and psu and int(_spec(psu, "wattage")) < int(_spec(gpu, "recommended_psu_watts")):
        issues.append(
            CompatibilityIssue(
                code="PSU_POWER_INSUFFICIENT",
                message="Maitinimo šaltinio galios nepakanka vaizdo plokštei.",
                component_ids=[gpu.id, psu.id],
            )
        )

    if cpu and cooler:
        supported_sockets = _spec(cooler, "supported_sockets") or []
        if _spec(cpu, "socket") not in supported_sockets:
            issues.append(
                CompatibilityIssue(
                    code="COOLER_SOCKET_MISMATCH",
                    message="Aušintuvas nepalaiko procesoriaus lizdo.",
                    component_ids=[cpu.id, cooler.id],
                )
            )
        elif int(_spec(cooler, "tdp_capacity_watts")) < int(_spec(cpu, "tdp_watts")):
            issues.append(
                CompatibilityIssue(
                    code="COOLER_CAPACITY_INSUFFICIENT",
                    message="Aušintuvo šiluminė galia yra per maža procesoriui.",
                    component_ids=[cpu.id, cooler.id],
                )
            )

    total = sum(
        (
            min((offer.price for offer in component.offers if offer.in_stock), default=Decimal(0))
            for component in build.components
        ),
        start=Decimal(0),
    )

    return CompatibilityRead(
        build_id=build.id,
        compatible=not issues,
        complete=not missing,
        total_price=total,
        missing_categories=missing,
        issues=issues,
    )
