.syntax unified
.thumb
.cpu cortex-m3

.include "stm32f10x.inc"

.equ StackPointer, 0x20008000

.section .text

.word StackPointer
.word Reset + 1

Reset:
	mov r1, RCC_APB2ENR_IOPCEN
	ldr r2, =RCC_APB2ENR
	str r1, [r2]

	mov r1, GPIO_CRH_MODE13
	ldr r2, =GPIOC_CRH
	str r1, [r2]

Loop:
	mov r1, GPIO_ODR_ODR13
	ldr r2, =GPIOC_ODR
	str r1, [r2]

	BL	Delay

	mov r1, 0
	ldr r2, =GPIOC_ODR
	str r1, [r2]

	BL Delay
B Loop

Delay:
	ldr r2, =0x00100000

Delay_loop:
	subs r2, r2, 1
	BNE Delay_loop
	BX LR
	