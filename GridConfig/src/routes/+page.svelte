<script lang="ts">
	import { onMount } from 'svelte';

	function createSvg(tagName: string) {
		var svgNS = 'http://www.w3.org/2000/svg';
		return document.createElementNS(svgNS, tagName);
	}

	let grid = function (
		numberPerSide: number,
		size: number,
		pixelsPerSide: number,
		colors: string[]
	) {
		let svg = createSvg('svg');
		svg.setAttribute('width', pixelsPerSide.toString());
		svg.setAttribute('height', pixelsPerSide.toString());
		svg.setAttribute('viewBox', [0, 0, numberPerSide * size, numberPerSide * size].join(' '));

		for (let i = 0; i < numberPerSide; i++) {
			for (let j = 0; j < numberPerSide; j++) {
				let color1 = colors[(i + j) % colors.length];
				let color2 = colors[(i + j + 1) % colors.length];
				let g = createSvg('g');
				g.setAttribute('transform', ['translate(', i * size, ',', j * size, ')'].join(''));
				var number = numberPerSide * i + j;
				var box = createSvg('rect');
				box.setAttribute('width', size.toString());
				box.setAttribute('height', size.toString());
				box.setAttribute('fill', color1);
				box.setAttribute('id', 'b' + number);
				g.appendChild(box);
				var text = createSvg('text');
				text.appendChild(document.createTextNode((i * numberPerSide + j).toString()));
				text.setAttribute('fill', color2);
				text.setAttribute('font-size', '4');
				text.setAttribute('x', '0');
				text.setAttribute('y', (size / 2).toString());
				text.setAttribute('id', 't' + number);
				g.appendChild(text);
				svg.appendChild(g);
			}
		}
		svg.addEventListener(
			'click',
			function (e) {
				let target = e.target as HTMLElement | null;
				let id = target?.id;
				if (id) alert(id.substring(1));
			},
			false
		);
		svg.addEventListener(
			'mousemove',
			(e) => {
				let target = e.target as HTMLElement | null;
				console.log(target?.id?.substring(1) ?? 'NOID');
			},
			false
		);
		return svg;
	};

	onMount(() => {
		let container = document.getElementById('container') as HTMLElement;
		container.appendChild(grid(5, 10, 250, ['red', 'white']));
	});
</script>

<h1 class="text-xl">HONR 313 Agent-Based Modeling Grid Configurator</h1>
<div id="container"></div>
