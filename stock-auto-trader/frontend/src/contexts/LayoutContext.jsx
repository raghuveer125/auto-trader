import { createContext, useCallback, useContext, useRef, useState } from 'react';

const LayoutContext = createContext();

export const useLayout = () => {
  const context = useContext(LayoutContext);
  if (!context) {
    throw new Error('useLayout must be used within LayoutProvider');
  }
  return context;
};

export const LayoutProvider = ({ children }) => {
  const [cards, setCards] = useState({});
  const cardsRef = useRef({});

  const registerCard = useCallback((id, element, initialPosition = { x: 0, y: 0 }) => {
    cardsRef.current[id] = {
      element,
      position: initialPosition,
      isDragging: false
    };
    setCards({ ...cardsRef.current });
  }, []);

  const unregisterCard = useCallback((id) => {
    delete cardsRef.current[id];
    setCards({ ...cardsRef.current });
  }, []);

  const checkCollision = (rect1, rect2) => {
    return !(
      rect1.right < rect2.left ||
      rect1.left > rect2.right ||
      rect1.bottom < rect2.top ||
      rect1.top > rect2.bottom
    );
  };

  const resolveCollisions = (draggedId, draggedRect, draggedPosition, depth = 0) => {
    const MARGIN = 20;
    const MAX_DEPTH = 5; // Prevent infinite recursion

    if (depth > MAX_DEPTH) return;

    const otherCards = Object.entries(cardsRef.current).filter(([id]) => id !== draggedId);

    // Calculate dragged card's rect with new position
    const draggedTestRect = {
      left: draggedPosition.x,
      top: draggedPosition.y,
      right: draggedPosition.x + draggedRect.width,
      bottom: draggedPosition.y + draggedRect.height
    };

    // Check each other card for collision
    for (const [otherId, otherCard] of otherCards) {
      if (!otherCard.element || otherCard.isDragging) continue;

      const otherRect = otherCard.element.getBoundingClientRect();
      const otherPos = otherCard.position;

      const otherTestRect = {
        left: otherPos.x,
        top: otherPos.y,
        right: otherPos.x + otherRect.width,
        bottom: otherPos.y + otherRect.height
      };

      if (checkCollision(draggedTestRect, otherTestRect)) {
        // Determine push direction based on drag direction and overlap
        const centerDraggedX = draggedTestRect.left + draggedRect.width / 2;
        const centerDraggedY = draggedTestRect.top + draggedRect.height / 2;
        const centerOtherX = otherTestRect.left + otherRect.width / 2;
        const centerOtherY = otherTestRect.top + otherRect.height / 2;

        const deltaX = centerDraggedX - centerOtherX;
        const deltaY = centerDraggedY - centerOtherY;

        // Push in the direction of the dragged card's center relative to other card
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
          // Push horizontally
          if (deltaX > 0) {
            // Push other card left
            otherCard.position = {
              ...otherPos,
              x: draggedPosition.x - otherRect.width - MARGIN
            };
          } else {
            // Push other card right
            otherCard.position = {
              ...otherPos,
              x: draggedPosition.x + draggedRect.width + MARGIN
            };
          }
        } else {
          // Push vertically
          if (deltaY > 0) {
            // Push other card up
            otherCard.position = {
              ...otherPos,
              y: draggedPosition.y - otherRect.height - MARGIN
            };
          } else {
            // Push other card down
            otherCard.position = {
              ...otherPos,
              y: draggedPosition.y + draggedRect.height + MARGIN
            };
          }
        }

        // Recursively check if the moved card now collides with others
        resolveCollisions(otherId, otherRect, otherCard.position, depth + 1);
      }
    }
  };

  const updateCardPosition = useCallback((id, newPosition, isDragging = false) => {
    if (!cardsRef.current[id]) return;

    const element = cardsRef.current[id].element;
    if (!element) return;

    const rect = element.getBoundingClientRect();

    // Update the dragged card's position
    cardsRef.current[id].position = newPosition;
    cardsRef.current[id].isDragging = isDragging;

    // Always resolve collisions (both during and after dragging)
    resolveCollisions(id, rect, newPosition);

    setCards({ ...cardsRef.current });
  }, []);

  const getCardPosition = useCallback((id) => {
    return cardsRef.current[id]?.position || { x: 0, y: 0 };
  }, []);

  return (
    <LayoutContext.Provider
      value={{
        cards,
        registerCard,
        unregisterCard,
        updateCardPosition,
        getCardPosition
      }}
    >
      {children}
    </LayoutContext.Provider>
  );
};

