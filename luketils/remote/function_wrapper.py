from dataclasses import dataclass
from typing import Any, Callable

import cloudpickle


@dataclass(frozen=True)
class CloudPickleFriendlyFunctionWrapper:
    func: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    def __getstate__(self) -> bytes:
        return cloudpickle.dumps((self.func, self.args, self.kwargs))

    def __setstate__(self, state: bytes) -> None:
        func, args, kwargs = cloudpickle.loads(state)
        object.__setattr__(self, "func", func)
        object.__setattr__(self, "args", args)
        object.__setattr__(self, "kwargs", kwargs)

    def execute(self) -> Any:
        return self.func(*self.args, **self.kwargs)


def serialize_function_for_execution(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> bytes:
    wrapper = CloudPickleFriendlyFunctionWrapper(
        func=func,
        args=args,
        kwargs=kwargs,
    )
    return cloudpickle.dumps(wrapper)


def execute_bytes_as_cloudpickle_wrapper(wrapper_bytes: bytes) -> Any:
    unpickled_wrapper = cloudpickle.loads(wrapper_bytes)
    if not isinstance(unpickled_wrapper, CloudPickleFriendlyFunctionWrapper):
        raise TypeError(
            f"Expected unpickled object to be CloudPickleFriendlyFunctionWrapper, "
            f"got {type(unpickled_wrapper).__name__}"
        )
    result = unpickled_wrapper.execute()
    return result

