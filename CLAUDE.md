# Claude Development Notes

This file documents design decisions and coding preferences for this project.

## Code Style Preferences

### Default Parameters

**Preference**: When there's an implementation class and a top-level user-friendly API, only provide default parameters in the top-level API.

- The top-level user-facing API may have default parameters for convenience
- Implementation classes and their methods should require all parameters to be explicitly passed
- Internal helper functions should require all parameters to be explicitly passed
- This makes data flow more explicit and reduces hidden dependencies
- Easier to trace where values come from when debugging

**Example**: A public `@profile` decorator might have default parameters, but the implementation class it instantiates and any internal helper functions should require all parameters to be passed explicitly.
