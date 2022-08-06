"""
Created on August 03, 2022

@authors: Philipp Deibert
"""
from typing import Callable, Any
from functools import wraps
from spflow.meta.structure.module import MetaModule
from spflow.meta.contexts.dispatch_context import DispatchContext, default_dispatch_context


def swappable(f) -> Callable:
    """Swappable decorator.

    Wraps a function in order to automatically check the dispatch context for specified alternative functions for a given module type.
    Assumes that the first argument is a module that is used as the key for checking for alternative functions.

    Returns:
        Wrapped function that automatically checks for alternative functions.
    """
    @wraps(f)
    def swappable_f(*args, **kwargs) -> Any:

        # ----- retrieve MetaModule that is dispatched on -----

        # first argument is the key
        key = args[0]

        if not isinstance(key, MetaModule):
            raise ValueError(f"First argument is expected to be of type {MetaModule}, but was {type(key)}.")

        # ----- retrieve DispatchContext -----

        # look in kwargs
        if "dispatch_ctx" in kwargs:
            dispatch_ctx = kwargs["dispatch_ctx"]
        # look in args
        else:
            dispatch_ctx = None
            _args = []

            for arg in args:
                if isinstance(arg, DispatchContext):
                    
                    # check if another dispatch context has been found before
                    if dispatch_ctx is not None:
                        raise LookupError(f"Multiple positional candidates of type {DispatchContext} found. Cannot determine which one to use.")
                    
                    dispatch_ctx = kwargs["dispatch_ctx"] = arg
                else:
                    # append argument to list of non-DispatchContext arguments
                    _args.append(arg)
            
            # replace args with argument list without dispatch context (makes retrieving it easier in subsequent recursions)
            args = _args

        # check if dispatch context is 'None'
        if dispatch_ctx is None:
            dispatch_ctx = default_dispatch_context()

        # ----- swapping -----

        _f = f

        # check if alternative function is given for module type in dispatch context
        if type(key) in dispatch_ctx.funcs:

            _f = dispatch_ctx.funcs[type(key)]

        return _f(*args, **kwargs)
    
    return swappable_f