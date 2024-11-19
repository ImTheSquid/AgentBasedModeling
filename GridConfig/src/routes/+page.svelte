<script lang="ts">
	import { onMount } from 'svelte';
	import { CellType, cellTypeKeys, colorForCell, type Cell } from '$lib';
	import { SvelteSet } from 'svelte/reactivity';

	function createSvg(tagName: string) {
		var svgNS = 'http://www.w3.org/2000/svg';
		return document.createElementNS(svgNS, tagName);
	}

	let grid = function (numberPerSide: number, size: number, pixelsPerSide: number) {
		let svg = createSvg('svg');
		svg.setAttribute('width', pixelsPerSide.toString());
		svg.setAttribute('height', pixelsPerSide.toString());
		svg.setAttribute('viewBox', [0, 0, numberPerSide * size, numberPerSide * size].join(' '));

		for (let i = 0; i < numberPerSide; i++) {
			for (let j = 0; j < numberPerSide; j++) {
				var number = `${i}, ${j}`;
				let cellData = number in gridData ? gridData[number] : null;
				let boxColor = selectedCells.has(number)
					? 'yellow'
					: cellData !== null
						? colorForCell(cellData.type)
						: 'white';
				let textColor = cellData !== null ? 'white' : 'black';
				let g = createSvg('g');
				g.setAttribute('transform', ['translate(', j * size, ',', i * size, ')'].join(''));
				var box = createSvg('rect');
				box.setAttribute('width', size.toString());
				box.setAttribute('height', size.toString());
				box.setAttribute('fill', boxColor);
				box.setAttribute('style', 'stroke-width:1;stroke:rgb(0,0,0);');
				box.setAttribute('id', number.toString());
				g.appendChild(box);
				if (showNumbers) {
					var text = createSvg('text');
					text.appendChild(document.createTextNode((i * numberPerSide + j).toString()));
					text.setAttribute('fill', textColor);
					text.setAttribute('font-size', '4');
					text.setAttribute('x', '1');
					text.setAttribute('y', (size / 2 + 1).toString());
					text.setAttribute('id', number.toString());
					text.setAttribute('style', 'user-select: none;');
					g.appendChild(text);
				}
				svg.appendChild(g);
			}
		}
		svg.addEventListener(
			'click',
			function (e) {
				let target = e.target as HTMLElement | null;
				let id = target?.id;
				if (!id) return;

				if (inSelectionMode) {
					selectedCells.add(id);
					return;
				}

				// Is there already grid data for this cell?
				if (id in gridData) {
					if (gridData[id].type == cellTypeKeys.length - 1) {
						delete gridData[id];
					} else {
						gridData[id].type += 1;
						gridData[id].associatedExit = null;
					}
				} else {
					gridData[id] = {
						type: 0,
						associatedExit: [-1, -1] as [number, number]
					};
				}
			},
			false
		);
		svg.addEventListener(
			'mousemove',
			(e) => {
				let target = e.target as HTMLElement | null;
				if (!target?.id) return;
				if (inSelectionMode && activeSelect) {
					selectedCells.add(target.id);
				}
			},
			false
		);
		svg.addEventListener('mousedown', (_) => {
			console.log('mousedown');
			activeSelect = true;
		});
		svg.addEventListener('mouseup', (_) => {
			activeSelect = false;
		});
		return svg;
	};

	let gridData: Record<string, Cell> = $state({});
	let selectedCells: SvelteSet<string> = $state(new SvelteSet());
	let sideLength: number = $state(5);
	let showNumbers: boolean = $state(true);
	let inSelectionMode: boolean = $state(false);
	let activeSelect: boolean = $state(false);

	$effect(() => {
		sideLength = Math.max(sideLength, 1);
		let container = document.getElementById('container') as HTMLElement;
		container.innerHTML = '';
		container.appendChild(grid(sideLength, 10, Math.max(sideLength * 50, 250)));
	});

	function clearSelection() {
		selectedCells.clear();
	}

	function setAllSelectedToType(cellType: CellType | null) {
		if (cellType === null) {
			for (let item of selectedCells) {
				delete gridData[item];
			}
		} else {
			for (let item of selectedCells) {
				if (cellType == CellType.Entrance && gridData[item]?.type != CellType.Entrance) {
					gridData[item] = {
						type: CellType.Entrance,
						associatedExit: [-1, -1] as [number, number]
					};
				} else if (cellType != CellType.Entrance) {
					gridData[item] = {
						type: cellType,
						associatedExit: null
					};
				}
			}
		}
		inSelectionMode = false;
		clearSelection();
	}
</script>

<h1 class="text-xl">HONR 313 Agent-Based Modeling Grid Configurator</h1>
<button
	class={`${inSelectionMode ? 'bg-red-300' : 'bg-gray-300'} p-2`}
	onclick={(_) => (inSelectionMode = !inSelectionMode)}>Toggle Selection</button
>
<button class="bg-gray-300 p-2" onclick={(_) => clearSelection()}>Clear Selection</button>
<label for="length">Num per side:</label>
<input id="length" bind:value={sideLength} type="number" />
<label for="showNumbers">Show numbers:</label>
<input id="showNumbers" bind:checked={showNumbers} type="checkbox" />
<p>KEY:</p>
{#if inSelectionMode}
	<button class="bg-gray-300" onclick={(_) => setAllSelectedToType(null)}>CLEAR</button>
{/if}
<ul>
	{#each cellTypeKeys as k, i}
		<li style={`color: ${colorForCell(i as CellType)};`}>
			{#if inSelectionMode}
				<button class="bg-gray-300" onclick={(_) => setAllSelectedToType(i as CellType)}>{k}</button
				>
			{:else}
				{k}
			{/if}
		</li>
	{/each}
</ul>
<div id="container"></div>
