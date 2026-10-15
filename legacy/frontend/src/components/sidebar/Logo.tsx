import { APP } from "@/constants/strings";

const Logo = () => (
  <div className="flex items-center gap-2">
    <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold">
      V
    </div>
    <span className="font-semibold text-sm tracking-tight">{APP.NAME}</span>
  </div>
);

export default Logo;
