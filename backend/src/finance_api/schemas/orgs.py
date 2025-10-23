from finance_api.schemas.schema import BaseSchema


class OrganizationSchema(BaseSchema):
    id: str
    domain: str
    sfin_url: str
    url: str = ""
    name: str = ""

    model_config = {"from_attributes": True}