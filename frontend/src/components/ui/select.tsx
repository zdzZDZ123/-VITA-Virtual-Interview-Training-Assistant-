import React from 'react';
import { cn } from '../../utils/cn';

interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

interface SelectContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface SelectItemProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
  children: React.ReactNode;
}

interface SelectValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  placeholder?: string;
}

const SelectContext = React.createContext<{
  value?: string;
  onValueChange?: (value: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}>({ isOpen: false, setIsOpen: () => {} });

const Select = React.forwardRef<HTMLDivElement, SelectProps>(
  ({ value, defaultValue, onValueChange, children }, ref) => {
    const [internalValue, setInternalValue] = React.useState(defaultValue || '');
    const [isOpen, setIsOpen] = React.useState(false);
    const currentValue = value !== undefined ? value : internalValue;
    
    const handleValueChange = (newValue: string) => {
      if (value === undefined) {
        setInternalValue(newValue);
      }
      onValueChange?.(newValue);
      setIsOpen(false);
    };

    return (
      <SelectContext.Provider value={{ 
        value: currentValue, 
        onValueChange: handleValueChange,
        isOpen,
        setIsOpen
      }}>
        <div ref={ref} className="relative">
          {children}
        </div>
      </SelectContext.Provider>
    );
  }
);
Select.displayName = "Select";

const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectTriggerProps>(
  ({ className, children, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    return (
      <button
        ref={ref}
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        onClick={() => context.setIsOpen(!context.isOpen)}
        {...props}
      >
        {children}
        <svg
          className={cn(
            "h-4 w-4 opacity-50 transition-transform",
            context.isOpen && "rotate-180"
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    );
  }
);
SelectTrigger.displayName = "SelectTrigger";

const SelectContent = React.forwardRef<HTMLDivElement, SelectContentProps>(
  ({ className, children, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    if (!context.isOpen) return null;

    return (
      <div
        ref={ref}
        className={cn(
          "absolute top-full z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
SelectContent.displayName = "SelectContent";

const SelectItem = React.forwardRef<HTMLButtonElement, SelectItemProps>(
  ({ className, children, value, ...props }, ref) => {
    const context = React.useContext(SelectContext);
    const isSelected = context.value === value;

    return (
      <button
        ref={ref}
        className={cn(
          "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
          isSelected && "bg-accent text-accent-foreground",
          className
        )}
        onClick={() => context.onValueChange?.(value)}
        {...props}
      >
        {isSelected && (
          <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </span>
        )}
        {children}
      </button>
    );
  }
);
SelectItem.displayName = "SelectItem";

const SelectValue = React.forwardRef<HTMLSpanElement, SelectValueProps>(
  ({ className, placeholder, ...props }, ref) => {
    const context = React.useContext(SelectContext);

    return (
      <span
        ref={ref}
        className={cn("block truncate", className)}
        {...props}
      >
        {context.value || placeholder}
      </span>
    );
  }
);
SelectValue.displayName = "SelectValue";

export { Select, SelectTrigger, SelectContent, SelectItem, SelectValue };