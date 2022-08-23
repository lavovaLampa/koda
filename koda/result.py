from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, NoReturn, Optional, final

from koda._generics import A, B, FailT
from koda.maybe import Just, Nothing, nothing

if TYPE_CHECKING:  # pragma: no cover
    from koda.maybe import Maybe


class Result(Generic[A, FailT], ABC):
    val: A | FailT
    """Contained value or error"""

    @abstractmethod
    def apply(self, container: "Result[Callable[[A], B], FailT]") -> "Result[B, FailT]":
        """Apply function (if any) contained in given container to contained value (if any).

        Args:
            container:  `Result` containing function (if any) to apply

        Returns:
            `Ok(container.val(self.val))` if self is `Ok(val)` and container is `Ok(val)`.

            `Ok(val)` if self is `Ok(val)` and container is `Err(val)`.

            `Err(val)` if self is `Err(val)` and container is `Ok(val)`.

            `Err(val)` if self is `Err(val)` and container is `Err(val)`.
        """

    @abstractmethod
    def get(self) -> A:
        """Return contained value (if any), else raise an exception.

        Raises:
            ValueError: In case self does not contain a value

        Returns:
            `val` if self is `Ok(val)`.
            Raises exception if self is `Err(val)`.
        """

    @abstractmethod
    def get_or_else(self, fallback: A) -> A:
        """Return contained value (if any), else return `fallback`.

        Args:
            fallback:   Value to return in case self is `Err`

        Returns:
            `val` if self is `Ok(val)`.
            `fallback` if self is `Err(val)`.
        """

    @abstractmethod
    def flat_map(self, fn: Callable[[A], "Result[B, FailT]"]) -> "Result[B, FailT]":
        """Map contained value (if any) using `fn`, returning new `Result`.

        Args:
            fn: Function to apply to contained value (if any)

        Returns:
            `fn(val)` if self is `Ok(val)`.
            `Err(val)` if self is `Err(val)`.
        """

    @abstractmethod
    def flat_map_err(self, fn: Callable[[FailT], "Result[A, B]"]) -> "Result[A, B]":
        """Map contained error (if any) using `fn`, returning new `Result`.

        Args:
            fn: Function to apply to contained error (if any)

        Returns:
            `fn(val)` if self is `Err(val)`.
            `Ok(val)` if self is `Ok(val)`.
        """

    @abstractmethod
    def map(self, fn: Callable[[A], B]) -> "Result[B, FailT]":
        """Map contained value (if any) using `fn`.

        Args:
            fn: Function to apply to contained value (if any)

        Returns:
            `Ok(fn(val))` if self is `Ok(val)`.
            `Err(val)` if self is `Err(val)`.
        """

    @abstractmethod
    def map_err(self, fn: Callable[[FailT], B]) -> "Result[A, B]":
        """Map contained error value (if any) using `fn`.

        Args:
            fn: Function to apply to error value (if any)

        Returns:
            `Err(fn(val))` if self is `Err(val)`.
            `Ok(val) if self is `Ok(val)`.
        """

    @abstractmethod
    def swap(self) -> "Result[FailT, A]":
        """Swap the contained value type.

        Returns:
            `Ok(val)` if self is `Err(val)`.
            `Err(val)` if self is `Ok(val)`.
        """

    @abstractproperty
    def to_optional(self) -> Optional[A]:
        """Convert to `Optional`, discarding error(s).

        Returns:
            `val` if self is `Ok(val)`.
            `None` if self is `Err(val)`.
        """

    @abstractproperty
    def to_maybe(self) -> Maybe[A]:
        """Convert to `Maybe`, discarding error(s).

        Returns:
            `Just(val)` if self is `Ok(val)`.
            `Nothing` if self is `Err(val)`.
        """
        ...

    def __rshift__(self, other: Callable[[A], B]) -> "Result[B, FailT]":
        """Map contained value (if any) using `other`.

        Args:
            other: Function to apply to contained value (if any)

        Returns:
            `Ok(fn(val))` in case self is `Ok(val)`.
            `Err(val)` in case self is `Err(val)`.
        """
        return self.map(other)

    def __or__(self, other: Callable[[FailT], B]) -> "Result[A, B]":
        """Map contained error value (if any) using `other`.

        Args:
            other: Function to apply to error value (if any)

        Returns:
            `Err(fn(val))` in case self is `Err(val)`.
            `Ok(val) in case self is `Ok(val)`.
        """
        return self.map_err(other)

    def __invert__(self) -> A:
        """Return contained value (if any), else raise an exception.

        Raises:
            ValueError: In case self does not contain a value

        Returns:
            `val` if self is `Ok(val)`.
            Raises exception if self is `Err(val)`.
        """
        return self.get()


@final
@dataclass(frozen=True)
class Err(Result[Any, FailT]):
    val: FailT

    def apply(self, container: "Result[Callable[[Any], Any], FailT]") -> "Err[FailT]":
        return self

    def get(self) -> NoReturn:
        raise ValueError("Value missing in an `Err` variant.")

    def get_or_else(self, fallback: A) -> A:
        return fallback

    def flat_map(self, fn: Callable[[Any], "Result[Any, FailT]"]) -> "Err[FailT]":
        return self

    def flat_map_err(self, fn: Callable[[FailT], "Result[A, B]"]) -> "Result[A, B]":
        return fn(self.val)

    def map(self, fn: Callable[[Any], Any]) -> "Err[FailT]":
        return self

    def map_err(self, fn: Callable[[FailT], B]) -> "Err[B]":
        return Err(fn(self.val))

    def swap(self) -> "Ok[FailT]":
        return Ok(self.val)

    @property
    def to_optional(self) -> None:
        return None

    @property
    def to_maybe(self) -> "Nothing":
        return nothing

    def __invert__(self) -> NoReturn:
        return self.get()


@final
@dataclass(frozen=True)
class Ok(Result[A, Any]):
    val: A

    def apply(self, container: "Result[Callable[[A], B], FailT]") -> "Result[B, FailT]":
        if isinstance(container, Ok):
            return Ok(container.val(self.val))
        elif isinstance(container, Err):
            return container
        else:
            # This should never happen
            assert False

    def get(self) -> A:
        return self.val

    def get_or_else(self, fallback: A) -> A:
        return self.val

    def flat_map(self, fn: Callable[[A], "Result[B, FailT]"]) -> "Result[B, FailT]":
        return fn(self.val)

    def flat_map_err(self, fn: Callable[[Any], "Result[A, Any]"]) -> "Ok[A]":
        return self

    def map(self, fn: Callable[[A], B]) -> "Ok[B]":
        return Ok(fn(self.val))

    def map_err(self, fn: Callable[[Any], Any]) -> "Ok[A]":
        return self

    def swap(self) -> "Err[A]":
        return Err(self.val)

    @property
    def to_optional(self) -> A:
        return self.val

    @property
    def to_maybe(self) -> Just[A]:
        return Just(self.val)
