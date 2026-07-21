import pytest
from pydantic import BaseModel

from mei.infrastructure.llm.fake_adapter import FakeStructuredLLM


class _Widget(BaseModel):
    name: str


class _Gadget(BaseModel):
    name: str


async def test_returns_fixed_response_for_registered_task() -> None:
    llm = FakeStructuredLLM(responses={"make_widget": _Widget(name="sprocket")})

    result = await llm.generate_structured(
        task_name="make_widget",
        prompt_version="v1",
        input_text="anything",
        output_model=_Widget,
        metadata={},
    )

    assert result == _Widget(name="sprocket")


async def test_supports_input_dependent_callable_response() -> None:
    llm = FakeStructuredLLM(responses={"make_widget": lambda text: _Widget(name=text.upper())})

    result = await llm.generate_structured(
        task_name="make_widget",
        prompt_version="v1",
        input_text="sprocket",
        output_model=_Widget,
        metadata={},
    )

    assert result == _Widget(name="SPROCKET")


async def test_raises_for_unregistered_task() -> None:
    llm = FakeStructuredLLM(responses={})

    with pytest.raises(KeyError):
        await llm.generate_structured(
            task_name="unregistered",
            prompt_version="v1",
            input_text="anything",
            output_model=_Widget,
            metadata={},
        )


async def test_raises_when_response_type_does_not_match_output_model() -> None:
    llm = FakeStructuredLLM(responses={"make_widget": _Gadget(name="sprocket")})

    with pytest.raises(TypeError):
        await llm.generate_structured(
            task_name="make_widget",
            prompt_version="v1",
            input_text="anything",
            output_model=_Widget,
            metadata={},
        )
