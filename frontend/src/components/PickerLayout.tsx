import { Outlet } from "react-router-dom";
import PickerHeader from "@/components/PickerHeader";

export default function PickerLayout() {
  return (
    <div className="flex flex-col min-h-screen">
      <PickerHeader />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
