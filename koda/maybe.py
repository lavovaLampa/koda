from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Final, Generic, NoReturn, Optional

from koda._generics import A, B, FailT

if TYPE_CHECKING:  # pragma: no cover
    from koda.result import Err, Ok, Result


class Maybe(Generic[A], ABC):
    @abstractmethod
    def get(self) -> A:
        """Return contained value (if any), else raise an exception.

        Raises:
            ValueError: In case self does not contain a value

        Returns:
            `val` if self is `Just(val)`.
        """

    @abstractmethod
    def get_or_else(self, fallback: A) -> A:
        """Get the contained value (if any) or `fallback`.

        Args:
            fallback:   Fallback return value

        Returns:
            Contained value (if any), else `fallback`
        """

    @abstractmethod
    def map(self, fn: Callable[[A], B]) -> "Maybe[B]":
        """Map the contained value (if any) using `fn`.

        Args:
            fn: Callable used to map contained value

        Returns:
            Result of applying the `fn` to the contained value (if any)
        """

    @abstractmethod
    def flat_map(self, fn: Callable[[A], "Maybe[B]"]) -> "Maybe[B]":
        """Map the contained value (if any) using given callable (that returns Maybe).

        Args:
            fn: Callable used to map contained value

        Returns:
            Result of applying the `fn` to the contained value (if any)
        """

    @abstractmethod
    def apply(self, container: "Maybe[Callable[[A], B]]") -> "Maybe[B]":
        """Apply function from given container (if any) to the contained value (if any).

        Args:
            container:  `Maybe` object containing a compatible function (if any)

        Returns:
            Result of container function (if any) on the contained value (if any), else `Nothing`
        """

    @abstractproperty
    def to_optional(self) -> Optional[A]:
        """Convert to `Optional` type.

        Returns:
            Contained value (if any), else `None`
        """

    @abstractmethod
    def to_result(self, fail_obj: FailT) -> "Result[A, FailT]":
        """Convert to `Result` object.

        Args:
            fail_obj:   Object to use as an `Err` result type

        Returns:
            `Ok` object with contained value (if any), else
            `Err` object with `fail_obj` value
        """

    def __rshift__(self, other: Callable[[A], B]) -> "Maybe[B]":
        """Map the contained value (if any) using `fn`.

        Args:
            fn: Callable used to map contained value

        Returns:
            Result of applying the `fn` to the contained value (if any)
        """
        return self.map(other)

    def __invert__(self) -> A:
        """Return contained value (if any), else raise an exception.

        Raises:
            ValueError: In case self does not contain a value

        Returns:
            `val` if self is `Just(val)`.
        """
        return self.get()


class Nothing(Maybe[Any]):
    def __new__(cls) -> "Nothing":
        """
        Make `Nothing` a singleton, so we can do `is` checks if we want.
        """
        if not hasattr(cls, "_instance"):
            cls._instance = super(Nothing, cls).__new__(cls)
        return cls._instance

    def get(self) -> NoReturn:
        raise ValueError("Value missing in a `Nothing` variant.")

    def get_or_else(self, fallback: A) -> A:
        return fallback

    def map(self, fn: Callable[[Any], Any]) -> "Nothing":
        return self

    def flat_map(self, fn: Callable[[Any], "Maybe[Any]"]) -> "Nothing":
        return self

    def apply(self, container: "Maybe[Callable[[Any], Any]]") -> "Nothing":
        return self

    @property
    def to_optional(self) -> None:
        return None

    def to_result(self, fail_obj: FailT) -> "Err[FailT]":
        from koda.result import Err

        return Err(fail_obj)

    def __invert__(self) -> NoReturn:
        return self.get()


# just a pre-init-ed instance of nothing.
nothing: Final[Nothing] = Nothing()


@dataclass(frozen=True)
class Just(Maybe[A]):
    val: A
    """Contained value"""

    def get(self) -> A:
        return self.val

    def get_or_else(self, fallback: Any) -> A:
        return self.val

    def map(self, fn: Callable[[A], B]) -> "Just[B]":
        return Just(fn(self.val))

    def flat_map(self, fn: Callable[[A], "Maybe[B]"]) -> "Maybe[B]":
        return fn(self.val)

    def apply(self, container: "Maybe[Callable[[A], B]]") -> "Maybe[B]":
        if isinstance(container, Nothing):
            return nothing
        else:
            return Just(container.val(self.val))

    @property
    def to_optional(self) -> A:
        return self.val

    def to_result(self, fail_obj: Any) -> "Ok[A]":
        from koda.result import Ok

        return Ok(self.val)