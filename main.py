import os
import random
import sys
import pygame

WIDTH, HEIGHT = 400, 600
PLAYER_SIZE = 50
ENEMY_SIZE = 50
ENEMY_SPEED = 5
PLAYER_SPEED = 5


def main(max_frames=None):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snack Racer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    player = pygame.Rect(WIDTH//2 - PLAYER_SIZE//2, HEIGHT - 2*PLAYER_SIZE, PLAYER_SIZE, PLAYER_SIZE)
    enemies = []
    spawn_event = pygame.USEREVENT + 1
    pygame.time.set_timer(spawn_event, 700)

    distance = 0.0
    running = True
    frames = 0

    while running:
        dt = clock.tick(60) / 1000  # seconds
        distance += ENEMY_SPEED * dt * 5  # scale factor for distance

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == spawn_event:
                x = random.randint(0, WIDTH - ENEMY_SIZE)
                enemies.append(pygame.Rect(x, -ENEMY_SIZE, ENEMY_SIZE, ENEMY_SIZE))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.left > 0:
            player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] and player.right < WIDTH:
            player.x += PLAYER_SPEED
        if keys[pygame.K_UP] and player.top > 0:
            player.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN] and player.bottom < HEIGHT:
            player.y += PLAYER_SPEED

        for enemy in enemies[:]:
            enemy.y += ENEMY_SPEED
            if enemy.colliderect(player):
                running = False
            if enemy.top > HEIGHT:
                enemies.remove(enemy)

        screen.fill((30, 30, 30))
        pygame.draw.rect(screen, (255, 165, 0), player)  # snack
        for enemy in enemies:
            pygame.draw.rect(screen, (200, 0, 0), enemy)
        dist_text = font.render(f"Distance: {int(distance)}", True, (255, 255, 255))
        screen.blit(dist_text, (10, 10))
        pygame.display.flip()

        frames += 1
        if max_frames and frames >= max_frames:
            running = False

    pygame.quit()
    print("Game over! Distance traveled:", int(distance))


if __name__ == "__main__":
    # When running in headless mode (e.g., during tests), limit frames
    max_frames = 300 if os.environ.get("PYGAME_HEADLESS") else None
    main(max_frames)
