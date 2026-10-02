from __future__ import annotations

from fastapi import APIRouter, Depends

from app.rules.tiers import tier
from app.schemas.common import BranchOut, CustomerOut, SampleInteraction
from app.seed import SeedData, get_seed_data

router = APIRouter(tags=["reference data"])


@router.get("/api/branches", response_model=list[BranchOut])
def list_branches(seed: SeedData = Depends(get_seed_data)) -> list[BranchOut]:
    return [BranchOut(**b) for b in seed.branches]


@router.get("/api/customers", response_model=list[CustomerOut])
def list_customers(seed: SeedData = Depends(get_seed_data)) -> list[CustomerOut]:
    out = []
    for c in seed.customers:
        visits = seed.visits_for(c["id"])
        t = tier(c, visits)
        last_spend = visits[0]["spend"] if visits else None
        out.append(CustomerOut(
            id=c["id"], displayName=c["displayName"], branchId=c["branchId"],
            joinedOn=c["joinedOn"], tier=t, lastSpend=last_spend,
        ))
    return out


@router.get("/api/interactions", response_model=list[SampleInteraction])
def list_sample_interactions(seed: SeedData = Depends(get_seed_data)) -> list[SampleInteraction]:
    """The sample messages the demo UI's message picker offers. Every one of
    these has a matching replay fixture, so they work with no live Jev key."""
    return [SampleInteraction(**i) for i in seed.interactions]
