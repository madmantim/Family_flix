import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './HelpTooltip.css';

interface HelpItem {
  icon: string;
  label: string;
}

interface HelpTooltipProps {
  items: HelpItem[];
}

export function HelpTooltip({ items }: HelpTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className="help-tooltip-container" ref={tooltipRef}>
      <button
        className="help-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Help"
      >
        ?
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="help-tooltip"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
          >
            <div className="tooltip-arrow" />
            {items.map((item, i) => (
              <div key={i} className="help-item">
                <span className="help-icon">{item.icon}</span>
                <span className="help-label">{item.label}</span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
