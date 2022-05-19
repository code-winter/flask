import pydantic
import re
from error_handlers import HttpError


class CreateUserValidator(pydantic.BaseModel):
    username: str
    password: str
    email: str

    @pydantic.validator('password')
    def pass_length(cls, password):
        if len(password) < 8:
            raise ValueError('Password is too short!')
        return password

    @pydantic.validator('email')
    def validate_email(cls, email):
        email_regex = re.compile(r"(\w+|)@(\w+\.\w+)")
        if re.search(email_regex, email) is None:
            raise HttpError(400, 'This is not a valid email')
        return email


class CreateAdValidator(pydantic.BaseModel):
    title: str
    description: str
    owner_id: int
