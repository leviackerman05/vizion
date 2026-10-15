import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { APP } from "@/constants/strings";

const NotFound = () => (
  <div className="min-h-screen flex flex-col items-center justify-center bg-background gap-4">
    <h1 className="text-4xl font-bold">404</h1>
    <p className="text-muted-foreground">Page not found</p>
    <Button asChild>
      <Link to="/">Back to {APP.NAME}</Link>
    </Button>
  </div>
);

export default NotFound;
