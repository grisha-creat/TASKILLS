from pydantic import BaseModel, Field, field_validator


class RegisterForm(BaseModel):
    email: str = Field(min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        # bcrypt принимает не более 72 байт
        if len(v.encode()) > 72:
            raise ValueError("Пароль слишком длинный")
        return v


class UserOut(BaseModel):
    id: int
    email: str
    username: str

    model_config = {"from_attributes": True}
