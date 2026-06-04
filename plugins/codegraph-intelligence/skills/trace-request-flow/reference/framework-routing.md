# Framework Routing Reference

Use this reference when tracing request flow from route to handler.

## Common Route Anchors

- Express: `app.get`, `app.post`, `router.use`, `router.METHOD`, middleware arrays.
- FastAPI: `@app.get`, `@router.post`, dependency parameters and `Depends`.
- Flask: `@app.route`, blueprint routes and method lists.
- Django: `path`, `re_path`, `include`, class-based views and `.as_view()`.
- Rails: `routes.rb`, `resources`, `get/post`, controller actions.
- Laravel: `Route::get`, `Route::post`, `Route::resource`, controller tuples and middleware groups.
- Spring: `@RequestMapping`, `@GetMapping`, `@PostMapping`, controller classes.
- ASP.NET: `[Route]`, `[HttpGet]`, controller action methods.
- Go: `http.HandleFunc`, chi/gorilla/mux registrations, Gin route groups.
- Rust: Axum `.route`, Actix services, Rocket route attributes.
- SvelteKit/Next/Nuxt: file-system routes, server handlers and route modules.

## Trace Layers

When present, report flow in this order:

1. Route registration or file-system route.
2. Middleware, guards, dependencies or filters.
3. Handler/controller/action.
4. Service or domain layer.
5. Repository/data access layer.
6. External integrations such as network calls, queues, cache, file system or third-party APIs.
7. Response shaping, error handling and async boundaries.

## Evidence Rules

- Mark a step as **observed** when CodeGraph shows the call or route edge.
- Mark a step as **inferred** when it is based on framework convention, file naming or config.
- Mark a step as **unknown** when routing is dynamic, generated or outside the indexed files.

## Required Output Fields

- Start point and how it was identified.
- Ordered flow table.
- Observed vs inferred edges.
- Async or queue boundaries.
- External side effects.
- Error handling points.
- Missing graph coverage or ambiguous route candidates.
