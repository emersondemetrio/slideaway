# Kotlin / Android Mobile Review Reference

Condensed from the official Android Developers documentation, [Best practices for coroutines in Android](https://developer.android.com/kotlin/coroutines/coroutines-best-practices) and [Use Kotlin coroutines with lifecycle-aware components](https://developer.android.com/topic/libraries/architecture/coroutines). Applies once `apps/mobile/android` has real code - not yet built as of this writing.

## Coroutines and scope (highest-value checks)

- `GlobalScope.launch { ... }` anywhere - promotes hardcoded values, makes testing very hard, and the coroutine outlives everything, including the screen that started it. Should be `viewModelScope`, `lifecycleScope`, or an injected `CoroutineScope`.
- A `Dispatcher` hardcoded inside a class (`withContext(Dispatchers.IO)` baked into a repository) instead of injected as a constructor parameter with a sensible default - makes tests non-deterministic and harder to control.
- A suspend function that does blocking I/O or CPU work without wrapping it in `withContext(...)` - the caller has no way to know it needs to get off the main thread, and every caller has to remember to do it themselves instead of the function being main-safe by construction.
- Business logic exposed as a suspend function directly from a `ViewModel`, rather than the `ViewModel` itself calling `viewModelScope.launch { ... }` internally - loses automatic cancellation on `ViewModel` clearing and configuration-change survival.
- A `MutableStateFlow`/`MutableSharedFlow` exposed directly instead of the read-only `StateFlow`/`SharedFlow` view - callers outside the owning class can mutate state they shouldn't.
- `try/catch` around coroutine code that catches a bare `Exception` (or `Throwable`) without re-throwing `CancellationException` - swallowing cancellation breaks structured concurrency; a caught `CancellationException` must always be re-thrown.
- A long-running loop or repeated operation inside a coroutine with no `ensureActive()`/`isActive` check - cancellation is cooperative, so a coroutine that never suspends or checks can run long after it should have stopped.

## Jetpack Compose / lifecycle

- A coroutine or callback started directly in composable body code instead of inside `LaunchedEffect`/`DisposableEffect` - runs on every recomposition instead of being tied to the composable's lifecycle.
- A `Flow` collected in Compose via `.collectAsState()` on a flow that should respect the lifecycle, instead of `collectAsStateWithLifecycle()` - keeps collecting (and doing work) even when the screen isn't visible.
- Event-handler coroutines started from `rememberCoroutineScope()` doing work that should actually be scoped to the ViewModel (i.e. should survive the composable being torn down) - or the reverse, ViewModel-scoped work that's actually meant to be tied to this specific composition.

## General Kotlin

- Long functions, high cyclomatic complexity, or obvious architectural smells that a linter would flag - `detekt` and `ktlint` are the standard tools for this, worth confirming CI runs them once the mobile app has real code.
- Idiomatic Kotlin basics: nullable types used defensively instead of enforcing non-null at the boundary, `!!` non-null assertions on values that can plausibly be null, data classes used for simple value holders vs. plain classes with manual `equals`/`hashCode`.
