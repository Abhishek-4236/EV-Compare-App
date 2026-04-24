import { create } from 'zustand';

const useCompare = create((set) => ({
  compareItems: [],
  toggleCompare: (vehicle) =>
    set((state) => {
      const exists = state.compareItems.find((v) => v.id === vehicle.id);
      if (exists) {
        return { compareItems: state.compareItems.filter((v) => v.id !== vehicle.id) };
      }
      if (state.compareItems.length >= 4) return state; // max 4
      return { compareItems: [...state.compareItems, vehicle] };
    }),
  removeCompare: (id) =>
    set((state) => ({
      compareItems: state.compareItems.filter((v) => v.id !== id),
    })),
  clearCompare: () => set({ compareItems: [] }),
}));

export default useCompare;
