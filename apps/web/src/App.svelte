<script>
  import Router from "svelte-spa-router";
  import ClaimInvite from "./routes/ClaimInvite.svelte";
  import Dashboard from "./routes/Dashboard.svelte";
  import Display from "./routes/Display.svelte";
  import Login from "./routes/Login.svelte";
  import Viewer from "./routes/Viewer.svelte";

  const routes = {
    "/login": Login,
    "/claim-invite/:token": ClaimInvite,
    "/rooms/:roomId/viewer": Viewer,
    "/rooms/:roomId/display": Display,
    "/dashboard": Dashboard,
  };
</script>

<Router {routes} />
